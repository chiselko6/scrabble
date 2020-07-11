import asyncio
import json
import random
import string
from itertools import chain
from pathlib import Path
from random import choices
from threading import Thread
from time import sleep
from typing import List, MutableSet, Optional

from scrabble.game import BoardSettings, BoardWord, Bonus, GameState, LetterBag, WordDirection
from scrabble.game.api import (Event, GameInitEvent, GameInitParams, GameStartEvent, GameStartParams,
                               PlayerAddLettersEvent, PlayerAddLettersParams, PlayerMoveEvent)
from scrabble.game.constants import PLAYER_MAX_LETTERS
from scrabble.serializers.game.api import EventSchema
from scrabble.server import Server
from scrabble.transport import EventMessage, EventMessagePayload, EventStatus, WebsocketMessage

from .constants import gen_english_letters_distribution

__all__ = [
    'ServerEngine',
]


class ServerEngine:

    def __init__(self, load_game_id: Optional[int] = None) -> None:
        self._events: List[Event] = []
        self._players: MutableSet[str] = set()
        self._server = Server(on_new_conn=self._on_new_conn,
                              on_new_msg=self._on_new_msg,
                              on_end_conn=self._on_end_conn)

        if load_game_id is not None:
            self._game_id = load_game_id
            self._load_events(load_game_id)
        else:
            self._game_id = random.randint(1, 1000)

        print(f'Starting game #{self._game_id}')

    @property
    def game_state(self) -> GameState:
        return GameState(self._game_id, events=self._events)

    @property
    def game_id(self) -> int:
        return self.game_state.game_id

    def _on_new_msg(self, player: str, msg: WebsocketMessage) -> None:
        if isinstance(msg, EventMessage):
            if msg.status == EventStatus.REQUESTED:
                self._apply_event(msg.payload.event)

                event = msg.payload.event
                if isinstance(event, PlayerMoveEvent):
                    player_username = event.params.player

                    player_state = self.game_state.get_player_state(player_username)
                    new_letters = choices(string.ascii_lowercase, k=PLAYER_MAX_LETTERS - len(player_state.letters))
                    if new_letters:
                        add_letters_event = PlayerAddLettersEvent(
                            params=PlayerAddLettersParams(player=player_username, letters=new_letters),
                            sequence=self.game_state.latest_event_sequence + 1,
                            game_id=self.game_id,
                        )
                        self._apply_event(add_letters_event)

    def _on_new_conn(self, player: str) -> None:
        print('New player', player)
        self._players.add(player)

        for event in self._events:
            self._send(player, self._wrap_event(event))

    def _on_end_conn(self, player: str) -> None:
        print('Disconnected player', player)
        self._players.remove(player)

    def _publish(self, msg: WebsocketMessage) -> None:
        self._server_loop.create_task(self._server.publish(msg))

    def _send(self, player: str, msg: WebsocketMessage) -> None:
        self._server_loop.create_task(self._server.send_player(player, msg))

    def _wrap_event(self, event: Event) -> EventMessage:
        return EventMessage(payload=EventMessagePayload(event=event), status=EventStatus.APPROVED)

    def _get_file_path(self, game_id: int) -> str:
        directory = '/tmp/scrabble/'
        filename = f'{game_id}_events.json'
        Path(directory).mkdir(parents=True, exist_ok=True)

        return f'{directory}{filename}'

    def _save_event(self, event: Event) -> None:
        with open(self._get_file_path(self.game_id), 'w') as fout:
            serialized_events = [EventSchema().dump(event) for event in self._events]
            json.dump(serialized_events, fout)

    def _load_events(self, game_id: int) -> None:
        with open(self._get_file_path(game_id), 'r') as fin:
            serialized_events = json.load(fin)
            events = [EventSchema().load(event) for event in serialized_events]
            for event in events:
                try:
                    self.game_state.apply_event(event)
                except Exception as e:
                    print('Error loading events', repr(e))
                    self._events = []
                    return

                self._events.append(event)

    def load_game(self, game_id: int) -> None:
        self._load_events(game_id)
        self._game_id = game_id

    def _apply_event(self, event: Event) -> None:
        try:
            self.game_state.apply_event(event)
        except Exception as e:
            print('Error applying event', repr(e))
        else:
            self._events.append(event)
            self._save_event(event)
            event_msg = self._wrap_event(event)
            self._publish(event_msg)

    def _run_server(self, host: Optional[str], port: int) -> None:
        self._server_loop = loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._server.start(host, port))
        loop.run_forever()

    def _cmd(self):
        started = len(self._events) > 0
        while True:
            cmd = input()
            if cmd == 'q':
                break
            elif cmd.startswith('start'):
                assert len(cmd.split()) == 2

                initial_word = cmd.split()[1]

                if started:
                    print('Already started')
                    continue

                players = list(self._players)

                board_width = 20
                board_height = 20
                letter_bag = LetterBag(board_width * board_height, gen_english_letters_distribution())
                bonuses_left_top_positions = ((5, 5, 3), (7, 7, 2))

                sequence = 1
                game_init_event = GameInitEvent(
                    sequence=sequence,
                    game_id=self.game_id,
                    params=GameInitParams(
                        players=players,
                        letters=list(letter_bag),
                        board_settings=BoardSettings(
                            width=board_width,
                            height=board_height,
                            init_word=BoardWord(
                                word=initial_word,
                                start_x=(board_width - len(initial_word)) // 2,
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
                self._apply_event(game_init_event)
                sequence += 1

                for player in players:
                    add_letters_event = PlayerAddLettersEvent(
                        game_id=self.game_id,
                        sequence=sequence,
                        params=PlayerAddLettersParams(
                            player=player,
                            letters=self.game_state.letters[:PLAYER_MAX_LETTERS],
                        )
                    )
                    self._apply_event(add_letters_event)
                    sequence += 1

                game_start_event = GameStartEvent(params=GameStartParams(player_to_start=players[0]),
                                                  sequence=sequence,
                                                  game_id=self.game_id)
                self._apply_event(game_start_event)
                sequence += 1

                started = True
            elif cmd.startswith('disconnect'):
                assert len(cmd.split()) == 2

                player = cmd.split()[1]
                self._server.disconnect(player)

    def run(self, host: Optional[str] = None, port: int = 5678) -> None:
        server_thread = Thread(target=self._run_server, args=(host, port))
        cmd_thread = Thread(target=self._cmd)

        server_thread.start()
        cmd_thread.start()

        cmd_thread.join()

        loop = self._server_loop
        loop.call_soon_threadsafe(loop.stop)
        while loop.is_running():
            sleep(0.2)

        loop.run_until_complete(self._server.stop())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        server_thread.join()
