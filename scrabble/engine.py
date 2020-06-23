import asyncio
import curses
import json
import random
import string
from pathlib import Path
from random import choices
from threading import Thread
from typing import Iterable, List, Optional, Tuple

from scrabble.client import Client
from scrabble.game import BoardSettings, BoardWord, BoardWords, Bonus, GameState, WordDirection
from scrabble.game.api import (Event, GameInitEvent, GameInitParams, GameStartEvent, GameStartParams,
                               PlayerAddLettersEvent, PlayerAddLettersParams, PlayerMoveEvent, PlayerMoveParams)
from scrabble.game.constants import PLAYER_MAX_LETTERS
from scrabble.gui.window import CallbackConfig, Window
from scrabble.serializers.game.api import EventSchema
from scrabble.server import Server
from scrabble.transport import (EndConnectionMessage, EventMessage, EventMessagePayload, EventStatus,
                                NewConnectionMessage, WebsocketMessage)

__all__ = [
    'ClientEngine',
    'ServerEngine',
]


class ClientEngine:

    def __init__(self, player: str, addr: Tuple[str, str], *, debug: bool = False) -> None:
        self._events: List[Event] = []
        self._player = player
        self._players = []
        self._window = Window(player, CallbackConfig(on_player_move=self._on_player_move))
        if debug:
            self._window.set_debug()

        self._client = Client(player, on_new_msg=self._on_client_msg,
                              on_connected=self._on_server_connected, on_disconnected=self._on_server_disconnected)
        self._client_loop = None

        self._server_addr = addr

    @property
    def game_state(self) -> GameState:
        return GameState(events=self._events)

    def _on_server_connected(self) -> None:
        self._window.player_connected(self._player)

    def _on_server_disconnected(self) -> None:
        for player in self._players:
            self._window.player_disconnected(player)

    def _on_player_move(self, words: Iterable[Tuple[int, int, str, str]], exchange_letters: List[str]) -> None:
        event_words = BoardWords()
        for player_word in words:
            event_words.add_word(BoardWord(start_x=player_word[0], start_y=player_word[1],
                                           word=player_word[2],
                                           direction=WordDirection.RIGHT
                                           if player_word[3] == 'right' else WordDirection.DOWN))

        event = PlayerMoveEvent(params=PlayerMoveParams(player=self._player,
                                                        words=event_words,
                                                        exchange_letters=exchange_letters),
                                sequence=self.game_state.latest_event_sequence + 1)

        try:
            print(f'Applying {event}')
            self.game_state.apply_event(event)
        except Exception as e:
            self._window.cancel_move()
            print(repr(e))
        else:
            self.send_event(event)

    def send_event(self, event: Event) -> None:
        self._client_loop.create_task(self._send(event))

    async def _send(self, event: Event) -> None:
        msg = EventMessage(payload=EventMessagePayload(event=event), status=EventStatus.REQUESTED)
        await self._client.send(msg)

    def _run_gui(self) -> None:
        curses.wrapper(self._window.run)

    def _run_client(self) -> None:
        loop = asyncio.new_event_loop()
        self._client_loop = loop
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._client.start(self._server_addr))
        loop.run_forever()

    def _on_client_msg(self, msg: WebsocketMessage) -> None:
        if isinstance(msg, EventMessage):
            self.handle_game_event(msg)
        elif isinstance(msg, NewConnectionMessage):
            self._window.player_connected(msg.payload.username)
        elif isinstance(msg, EndConnectionMessage):
            self._window.player_disconnected(msg.payload.username)

    def _apply_event(self, event: Event) -> None:
        try:
            self.game_state.apply_event(event)
        except Exception as e:
            print('Error applying event', repr(e))
        else:
            self._events.append(event)
            self._gui_apply_event(event)

    def handle_game_event(self, event_msg: EventMessage) -> None:
        if event_msg.status == EventStatus.APPROVED:
            event = event_msg.payload.event
            if event.sequence <= self.game_state.latest_event_sequence:
                return

            self._apply_event(event)

    def _gui_apply_event(self, event: Event) -> None:
        handlers = {
            GameInitEvent: self._gui_apply__game_init,
            GameStartEvent: self._gui_apply__game_start,
            PlayerAddLettersEvent: self._gui_apply__player_add_letters,
            PlayerMoveEvent: self._gui_apply__player_move,
        }
        handler = handlers.get(type(event))

        if handler is None:
            raise ValueError(f'Unknown event {event}')

        handler(event)

    def _gui_apply__game_init(self, event: GameInitEvent) -> None:
        for player in event.params.players:
            self._window.add_player(player)
            self._players.append(player)

        init_word = event.params.board_settings.init_word
        if init_word is not None:
            self._window.add_grid_word(init_word.start_x, init_word.start_y, init_word.word, init_word.direction.value)

        for bonus in event.params.board_settings.bonuses:
            self._window.add_bonus(bonus.location_x, bonus.location_y, bonus.multiplier)

    def _gui_apply__game_start(self, event: GameStartEvent) -> None:
        player_to_move = self.game_state.player_to_move
        assert player_to_move is not None

        self._window.set_player_turn(self.game_state.player_to_move)

    def _gui_apply__player_add_letters(self, event: PlayerAddLettersEvent) -> None:
        if self._player == event.params.player:
            self._window.update_player_letters(self.game_state.get_player_state(self._player).letters)

    def _gui_apply__player_move(self, event: PlayerMoveEvent) -> None:
        for word in event.params.words:
            self._window.add_grid_word(word.start_x, word.start_y, word.word, word.direction.value)
        score = self.game_state.get_player_score(event.params.player)
        self._window.update_player_score(event.params.player, score)
        self._window.set_player_turn(self.game_state.player_to_move)

    def run(self) -> None:
        gui_thread = Thread(target=self._run_gui)
        client_thread = Thread(target=self._run_client)

        gui_thread.start()
        client_thread.start()

        gui_thread.join()
        client_thread.join()


class ServerEngine:

    def __init__(self, game_id: Optional[str] = None) -> None:
        self._events: List[Event] = []
        self._server_loop = None
        self._server = Server(on_new_conn=self._on_new_conn, on_new_msg=self._on_new_msg)
        self._players = set()

        if game_id is not None:
            self._load_events(game_id)
            self._game_id = game_id
        else:
            self._game_id = str(random.randint(1, 1000))
            print(f'Starting game #{self._game_id}')

    @property
    def game_state(self) -> GameState:
        return GameState(events=self._events)

    @property
    def game_id(self) -> str:
        return self._game_id

    def _on_new_msg(self, player: str, msg: WebsocketMessage) -> None:
        if isinstance(msg, EventMessage):
            if msg.status == EventStatus.REQUESTED:
                self._apply_event(msg.payload.event)

                event = msg.payload.event
                if isinstance(event, PlayerMoveEvent):
                    player_username = event.params.player

                    player = self.game_state.get_player_state(player_username)
                    new_letters = choices(string.ascii_lowercase, k=PLAYER_MAX_LETTERS - len(player.letters))
                    if new_letters:
                        add_letters_event = PlayerAddLettersEvent(
                            params=PlayerAddLettersParams(player=player_username, letters=new_letters),
                            sequence=self.game_state.latest_event_sequence + 1,
                        )
                        self._apply_event(add_letters_event)

    def _on_new_conn(self, player: str) -> None:
        print('New player', player)
        self._players.add(player)

        for event in self._events:
            self._send(player, self._wrap_event(event))

    def _publish(self, msg: WebsocketMessage) -> None:
        self._server_loop.create_task(self._server.publish(msg))

    def _send(self, player: str, msg: WebsocketMessage) -> None:
        self._server_loop.create_task(self._server.send_player(player, msg))

    def _wrap_event(self, event: Event) -> EventMessage:
        return EventMessage(payload=EventMessagePayload(event=event), status=EventStatus.APPROVED)

    def _get_file_path(self, game_id: str) -> str:
        directory = '/tmp/scrabble/'
        filename = f'{game_id}_events.json'
        Path(directory).mkdir(parents=True, exist_ok=True)

        return f'{directory}{filename}'

    def _save_event(self, event: Event) -> None:
        with open(self._get_file_path(self.game_id), 'w') as fout:
            serialized_events = [EventSchema().dump(event) for event in self._events]
            json.dump(serialized_events, fout)

    def _load_events(self, game_id: str) -> None:
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

    def load_game(self, game_id: str) -> None:
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

    def _run_server(self):
        self._server_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._server_loop)

        self._server_loop.run_until_complete(self._server.start())
        self._server_loop.run_forever()

    def _cmd(self):
        started = len(self._events) > 0
        while True:
            cmd = input()
            if cmd.startswith('start'):
                assert len(cmd.split()) == 2

                initial_word = cmd.split()[1]

                if started:
                    print('Already started')
                    continue

                players = list(self._players)

                sequence = 1
                game_init_event = GameInitEvent(
                    sequence=sequence,
                    params=GameInitParams(
                        players=players,
                        board_settings=BoardSettings(
                            width=30,
                            height=30,
                            init_word=BoardWord(
                                word=initial_word,
                                start_x=(30 - len(initial_word)) // 2,
                                start_y=15,
                                direction=WordDirection.RIGHT,
                            ),
                            bonuses=[
                                Bonus(location_x=5, location_y=5, multiplier=3),
                                Bonus(location_x=25, location_y=25, multiplier=3),
                                Bonus(location_x=5, location_y=25, multiplier=3),
                                Bonus(location_x=25, location_y=5, multiplier=3),
                                Bonus(location_x=10, location_y=10, multiplier=2),
                                Bonus(location_x=10, location_y=20, multiplier=2),
                                Bonus(location_x=20, location_y=10, multiplier=2),
                                Bonus(location_x=20, location_y=20, multiplier=2),
                            ],
                        ),
                    ),
                )
                self._apply_event(game_init_event)
                sequence += 1

                for player in players:
                    add_letters_event = PlayerAddLettersEvent(
                        sequence=sequence,
                        params=PlayerAddLettersParams(
                            player=player,
                            letters=choices(string.ascii_lowercase, k=PLAYER_MAX_LETTERS),
                        )
                    )
                    self._apply_event(add_letters_event)
                    sequence += 1

                game_start_event = GameStartEvent(params=GameStartParams(player_to_start=players[0]), sequence=sequence)
                self._apply_event(game_start_event)
                sequence += 1

                started = True

    def run(self):
        server_thread = Thread(target=self._run_server)
        cmd_thread = Thread(target=self._cmd)

        server_thread.start()
        cmd_thread.start()

        cmd_thread.join()
        server_thread.join()
