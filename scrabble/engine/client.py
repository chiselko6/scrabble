import asyncio
import curses
from threading import Thread
from typing import Iterable, List, Tuple

from scrabble.client import Client
from scrabble.game import BoardWord, BoardWords, GameState, WordDirection
from scrabble.game.api import (Event, GameInitEvent, GameStartEvent, PlayerAddLettersEvent, PlayerMoveEvent,
                               PlayerMoveParams)
from scrabble.gui.window import CallbackConfig, Window
from scrabble.transport import (EndConnectionMessage, EventMessage, EventMessagePayload, EventStatus,
                                NewConnectionMessage, WebsocketMessage)

__all__ = [
    'ClientEngine',
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
