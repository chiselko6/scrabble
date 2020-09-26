import asyncio
import json
import logging
import logging.config
import random
from itertools import chain
from pathlib import Path
from threading import Thread
from time import sleep
from typing import List, MutableMapping, MutableSet, Optional

from scrabble.game import BoardSettings, BoardWord, Bonus, GameState, LetterBag, WordDirection
from scrabble.game.api import (Event, GameInitEvent, GameInitParams, GameStartEvent, GameStartParams,
                               PlayerAddLettersEvent, PlayerAddLettersParams, PlayerMoveEvent)
from scrabble.game.constants import PLAYER_MAX_LETTERS
from scrabble.serializers.game.api import EventSchema
from scrabble.settings import SERVER_LOGGING_CONFIG
from scrabble.transport import (EventMessage, EventMessagePayload, EventStatus, PlayerConnectionID, Server,
                                WebsocketMessage)

from .constants import gen_english_letters_distribution

__all__ = [
    'ServerEngine',
]


class ServerEngine:

    def __init__(self) -> None:
        logging.config.dictConfig(SERVER_LOGGING_CONFIG)
        self._logger = logging.getLogger()

        self._players: MutableSet[PlayerConnectionID] = set()
        self._server = Server(on_new_conn=self._on_new_conn,
                              on_new_msg=self._on_new_msg,
                              on_end_conn=self._on_end_conn)

        self._events: MutableMapping[int, List[Event]] = {}

    def get_game_state(self, game_id: int) -> GameState:
        return GameState(game_id, events=self._events[game_id])

    def load_game(self, game_id: int) -> None:
        self._events[game_id] = []

        self._load_events(game_id)

        self._logger.info(f'Loaded game #{game_id}')

    def init_new_game(self) -> int:
        game_id = random.randint(1, 1000)
        self._events[game_id] = []

        return game_id

    def start_game(self, game_id: int, initial_word: str) -> None:
        if game_id not in self._events:
            raise RuntimeError('Game was not initialized')

        started = len(self._events[game_id]) > 0
        if started:
            raise RuntimeError('Game already started')

        players = [
            username
            for username, player_game_id in self._players
            if player_game_id == game_id
        ]

        board_width = 20
        board_height = 20
        letter_bag = LetterBag(board_width * board_height, gen_english_letters_distribution())
        bonuses_left_top_positions = ((5, 5, 3), (7, 7, 2))

        sequence = 1
        game_init_event = GameInitEvent(
            sequence=sequence,
            game_id=game_id,
            params=GameInitParams(
                players=players,
                letters=list(letter_bag),
                board_settings=BoardSettings(
                    width=board_width,
                    height=board_height,
                    init_word=BoardWord(
                        word=initial_word,
                        start_x=(board_width + 1 - len(initial_word)) // 2,
                        start_y=board_height // 2,
                        direction=WordDirection.RIGHT,
                    ),
                    bonuses=list(chain(*[
                        (
                            Bonus(location_x=x, location_y=y, multiplier=multiplier),
                            Bonus(location_x=x, location_y=board_height - y, multiplier=multiplier),
                            Bonus(location_x=board_width - x, location_y=board_height - y,
                                  multiplier=multiplier),
                            Bonus(location_x=board_width - x, location_y=y, multiplier=multiplier),
                        )
                        for x, y, multiplier in bonuses_left_top_positions
                    ])),
                ),
            ),
        )
        self._apply_event(game_id, game_init_event)
        sequence += 1

        for player in players:
            add_letters_event = PlayerAddLettersEvent(
                game_id=game_id,
                sequence=sequence,
                params=PlayerAddLettersParams(
                    player=player,
                    letters=self.get_game_state(game_id).letters[:PLAYER_MAX_LETTERS],
                )
            )
            self._apply_event(game_id, add_letters_event)
            sequence += 1

        game_start_event = GameStartEvent(params=GameStartParams(player_to_start=players[0]),
                                          sequence=sequence,
                                          game_id=game_id)
        self._apply_event(game_id, game_start_event)

        self._logger.info(f'Started game #{game_id}')

    def _on_new_msg(self, player_id: PlayerConnectionID, msg: WebsocketMessage) -> None:
        username, game_id = player_id

        if isinstance(msg, EventMessage):
            if msg.status == EventStatus.REQUESTED:
                self._apply_event(game_id, msg.payload.event)

                event = msg.payload.event
                if isinstance(event, PlayerMoveEvent):
                    player_username = event.params.player

                    game_state = self.get_game_state(game_id)
                    player_state = game_state.get_player_state(player_username)

                    need_letters_count = PLAYER_MAX_LETTERS - len(player_state.letters)
                    new_letters = game_state.letters[:need_letters_count]
                    if new_letters:
                        add_letters_event = PlayerAddLettersEvent(
                            params=PlayerAddLettersParams(player=player_username, letters=new_letters),
                            sequence=game_state.latest_event_sequence + 1,
                            game_id=game_id,
                        )
                        self._apply_event(game_id, add_letters_event)

    def _on_new_conn(self, player_id: PlayerConnectionID) -> None:
        username, game_id = player_id

        if game_id not in self._events:
            raise RuntimeError('Game was not initialized')

        self._logger.info(f'New player {player_id}')
        self._players.add(player_id)

        for event in self._events[game_id]:
            self._send(player_id, self._wrap_event(event))

    def _on_end_conn(self, player_id: PlayerConnectionID) -> None:
        self._logger.info(f'Disconnected player {player_id}')
        self._players.remove(player_id)

    def _publish(self, game_id: int, msg: WebsocketMessage) -> None:
        self._server_loop.create_task(self._server.publish_to_game(msg, game_id))

    def _send(self, player_id: PlayerConnectionID, msg: WebsocketMessage) -> None:
        self._server_loop.create_task(self._server.send_player(player_id, msg))

    def _wrap_event(self, event: Event) -> EventMessage:
        return EventMessage(payload=EventMessagePayload(event=event), status=EventStatus.APPROVED)

    def _get_file_path(self, game_id: int) -> str:
        directory = '/tmp/scrabble/'
        filename = f'{game_id}_events.json'
        Path(directory).mkdir(parents=True, exist_ok=True)

        return f'{directory}{filename}'

    def _save_event(self, game_id: int, event: Event) -> None:
        with open(self._get_file_path(game_id), 'w') as fout:
            serialized_events = [EventSchema().dump(event) for event in self._events[game_id]]
            json.dump(serialized_events, fout)

    def _load_events(self, game_id: int) -> None:
        try:
            with open(self._get_file_path(game_id), 'r') as fin:
                serialized_events = json.load(fin)
                events = [EventSchema().load(event) for event in serialized_events]
                for event in events:
                    try:
                        self.get_game_state(game_id).apply_event(event)
                    except Exception:
                        self._logger.exception('Error loading events')
                        del self._events[game_id]
                        return

                    self._events[game_id].append(event)

        except FileNotFoundError:
            raise RuntimeError('Cannot find the game')

    def _apply_event(self, game_id: int, event: Event) -> None:
        try:
            self.get_game_state(game_id).apply_event(event)
        except Exception:
            self._logger.exception('Error applying event')
        else:
            self._events[game_id].append(event)
            self._save_event(game_id, event)
            event_msg = self._wrap_event(event)
            self._publish(game_id, event_msg)

    def _run_server(self, host: Optional[str], port: int) -> None:
        self._server_loop = loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._server.start(host, port))
        loop.run_forever()

    def _cmd(self):
        while True:
            cmd = input()
            if cmd == 'q':
                break

            elif cmd == 'new':
                game_id = self.init_new_game()
                self._logger.info(f'Initialized new game #{game_id}')

            elif cmd.startswith('start'):
                assert len(cmd.split()) == 3

                game_id = int(cmd.split()[1])
                initial_word = cmd.split()[2]

                self.start_game(game_id, initial_word)

            elif cmd.startswith('load'):
                assert len(cmd.split()) == 2

                game_id = int(cmd.split()[1])

                self.load_game(game_id)

            elif cmd.startswith('disconnect'):
                assert len(cmd.split()) == 3

                game_id = int(cmd.split()[1])
                player = cmd.split()[2]
                self._server.disconnect((player, game_id))

    def _terminate(self) -> None:
        loop = self._server_loop

        loop.call_soon_threadsafe(loop.stop)
        while loop.is_running():
            sleep(0.2)

        loop.run_until_complete(self._server.stop())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    def run(self, host: Optional[str] = None, port: int = 5678) -> None:
        try:
            self._run_server(host, port)
        finally:
            self._terminate()

    def run_with_cmd(self, host: Optional[str] = None, port: int = 5678) -> None:
        server_thread = Thread(target=self._run_server, args=(host, port))
        cmd_thread = Thread(target=self._cmd)

        server_thread.start()
        cmd_thread.start()

        cmd_thread.join()

        self._terminate()

        server_thread.join()
