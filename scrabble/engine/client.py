import asyncio
import curses
import logging
import logging.config
from threading import Thread
from typing import Iterable, List, Tuple, cast

from scrabble.game import BoardWord, BoardWords, GameState, WordDirection
from scrabble.game.api import (Event, GameInitEvent, GameStartEvent, PlayerAddLettersEvent, PlayerMoveEvent,
                               PlayerMoveParams)
from scrabble.gui.window import CallbackConfig, Window
from scrabble.settings import CLIENT_LOGGING_CONFIG
from scrabble.transport import (Client, EndConnectionMessage, EventMessage, EventMessagePayload, EventStatus,
                                NewConnectionMessage, WebsocketMessage)

__all__ = [
    'ClientEngine',
]


class ClientEngine:

    def __init__(self, player: str, game_id: int) -> None:
        logging.config.dictConfig(CLIENT_LOGGING_CONFIG)
        self._logger = logging.getLogger()

        self._events: List[Event] = []
        self._player = player
        self._players: List[str] = []
        self._game_id = game_id
        self._window = Window(player, CallbackConfig(on_player_move=self._on_player_move))

        self._client = Client(player, game_id, on_new_msg=self._on_client_msg,
                              on_connected=self._on_server_connected, on_disconnected=self._on_server_disconnected)

    @property
    def game_state(self) -> GameState:
        return GameState(self._game_id, events=self._events)

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
                                sequence=self.game_state.latest_event_sequence + 1,
                                game_id=self.game_state.game_id)

        try:
            self._logger.debug(f'Applying event: {event}')
            self.game_state.apply_event(event)
        except Exception:
            self._window.cancel_move()
            self._logger.exception(f'Error on applying event {event}')
        else:
            self.send_event(event)

    def send_event(self, event: Event) -> None:
        self._client_loop.create_task(self._send(event))

    async def _send(self, event: Event) -> None:
        msg = EventMessage(payload=EventMessagePayload(event=event), status=EventStatus.REQUESTED)
        await self._client.send(msg)

    def _run_gui(self) -> None:
        curses.wrapper(self._window.run)

    def _run_client(self, host: str, port: int) -> None:
        loop = asyncio.new_event_loop()
        self._client_loop = loop
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._client.start((host, port)))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())

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
        except Exception:
            self._logger.exception(f'Error applying event {event}')
        else:
            self._events.append(event)
            self._gui_apply_event(event)

    def handle_game_event(self, event_msg: EventMessage) -> None:
        if event_msg.status == EventStatus.APPROVED:
            event = event_msg.payload.event

            if event.game_id != self.game_state.game_id:
                raise RuntimeError('Game ID is different')
            if event.sequence <= self.game_state.latest_event_sequence:
                return

            self._apply_event(event)

    def _gui_apply_event(self, event: Event) -> None:
        if isinstance(event, GameInitEvent):
            self._gui_apply__game_init(event)
        elif isinstance(event, GameStartEvent):
            self._gui_apply__game_start(event)
        elif isinstance(event, PlayerAddLettersEvent):
            self._gui_apply__player_add_letters(event)
        elif isinstance(event, PlayerMoveEvent):
            self._gui_apply__player_move(event)
        else:
            raise ValueError(f'Unknown event {event}')

    def _gui_apply__game_init(self, event: GameInitEvent) -> None:
        self._window.set_language(event.params.lang)

        for player in event.params.players:
            self._window.add_player(player)
            self._players.append(player)

        init_word = event.params.board_settings.init_word
        if init_word is not None:
            self._window.add_grid_words([
                (
                    init_word.start_x,
                    init_word.start_y,
                    init_word.word,
                    init_word.direction.value,
                ),
            ])

        for bonus in event.params.board_settings.bonuses:
            self._window.add_bonus(bonus.location_x, bonus.location_y, bonus.multiplier)

    def _gui_apply__game_start(self, event: GameStartEvent) -> None:
        self._window.set_player_turn(cast(str, self.game_state.player_to_move))

    def _gui_apply__player_add_letters(self, event: PlayerAddLettersEvent) -> None:
        if self._player == event.params.player:
            self._window.update_player_letters(self.game_state.get_player_state(self._player).letters)

    def _gui_apply__player_move(self, event: PlayerMoveEvent) -> None:
        added_words = [
            (word.start_x, word.start_y, word.word, word.direction.value)
            for word in event.params.words
        ]
        self._window.add_grid_words(added_words)

        score = self.game_state.get_player_score(event.params.player)
        self._window.update_player_score(event.params.player, score)
        self._window.set_player_turn(cast(str, self.game_state.player_to_move))

    def run(self, host: str, port: str) -> None:
        gui_thread = Thread(target=self._run_gui)
        client_thread = Thread(target=self._run_client, args=(host, port))

        gui_thread.start()
        client_thread.start()

        gui_thread.join()

        self._client.stop()
        client_thread.join()
