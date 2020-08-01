import curses
import json
from threading import Thread
from typing import List, Optional, cast

from scrabble.game import GameState
from scrabble.game.api import Event, GameInitEvent, GameStartEvent, PlayerAddLettersEvent, PlayerMoveEvent
from scrabble.gui.window import CallbackConfig, Window
from scrabble.serializers.game.api import EventSchema

__all__ = [
    'ReplayEngine',
]


class ReplayEngine:

    def __init__(self, game_id: int, events_filepath: str, player: str, sequence: Optional[int] = None) -> None:
        self._game_id = game_id
        self._events_filepath = events_filepath
        self._player = player
        self._sequence = sequence

        self._window = Window(self._player, CallbackConfig(on_player_move=self._on_player_move))
        self._window.set_debug()
        self._file_events: List[Event] = []
        self._events: List[Event] = []

    @property
    def game_state(self) -> GameState:
        return GameState(self._game_id, events=self._events)

    def _on_player_move(self, *args, **kwargs) -> None:
        ...

    def _apply_event(self, event: Event) -> None:
        try:
            self.game_state.apply_event(event)
        except Exception as e:
            print('Error applying event', repr(e))
        else:
            self._events.append(event)
            self._gui_apply_event(event)

    def _load_events(self, events_filepath: str) -> None:
        try:
            with open(events_filepath, 'r') as fin:
                serialized_events = json.load(fin)
                self._file_events = [EventSchema().load(event) for event in serialized_events]

        except FileNotFoundError:
            raise RuntimeError('Cannot find the game')

    def _run_gui(self) -> None:
        curses.wrapper(self._window.run)

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
        for player in event.params.players:
            self._window.add_player(player)

        init_word = event.params.board_settings.init_word
        if init_word is not None:
            self._window.add_grid_words([
                (init_word.start_x, init_word.start_y, init_word.word, init_word.direction.value),
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

    def run(self) -> None:
        gui_thread = Thread(target=self._run_gui)

        gui_thread.start()

        self._load_events(self._events_filepath)
        for event in self._file_events:
            if self._sequence is None or event.sequence <= self._sequence:
                self._apply_event(event)

        gui_thread.join()
