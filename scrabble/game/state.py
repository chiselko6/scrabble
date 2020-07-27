from operator import methodcaller
from typing import Iterable, List, MutableMapping, MutableSet, Optional

from .api import (Event, GameInitEvent, GameInitParams, GameStartEvent, GameStartParams, PlayerAddLettersEvent,
                  PlayerAddLettersParams, PlayerMoveEvent, PlayerMoveParams)
from .board import Board
from .constants import BONUS_FOR_ALL_LETTERS_USED, PLAYER_MAX_LETTERS
from .player import Player

__all__ = [
    'GameState',
]


class GameState:
    EVENT_MAP = {
        PlayerAddLettersEvent: 'player_add_letters',
        GameInitEvent: 'game_init',
        PlayerMoveEvent: 'player_move',
        GameStartEvent: 'game_start',
    }

    def __init__(self, game_id: int, *, events: Optional[Iterable[Event]] = None):
        self._players_order: List[Player] = []
        self._players_by_username: MutableMapping[str, Player] = {}
        self._players_connected: MutableSet[str] = set()
        self._player_idx_turn: Optional[int] = None
        self._letters: List[str] = []
        self._sequence = 0
        self._game_id = game_id

        if events:
            for event in events:
                self.apply_event(event)

    @property
    def latest_event_sequence(self) -> int:
        return self._sequence

    @property
    def letters(self) -> List[str]:
        return list(self._letters)

    @property
    def game_id(self) -> int:
        return self._game_id

    def apply_event(self, event: Event) -> None:
        if self.game_id != event.game_id:
            raise ValueError(f'Event belongs to the different game id ({self.game_id} != {event.game_id})')

        if self.latest_event_sequence + 1 != event.sequence:
            raise ValueError(f'Next event must have sequence = {self.latest_event_sequence + 1}, '
                             f'got {event.sequence}')

        try:
            event_type = self.EVENT_MAP[type(event)]
        except KeyError:
            raise ValueError(f'Unknown event {event}')

        self._sequence = event.sequence

        methodcaller(f'event__{event_type}', event.params)(self)

    @property
    def player_to_move(self) -> Optional[str]:
        if self._player_idx_turn is None:
            return None

        return self._players_order[self._player_idx_turn].username

    def get_player_state(self, player: str) -> Player:
        return self._players_by_username[player]

    def event__player_add_letters(self, params: PlayerAddLettersParams) -> None:
        player = self._players_by_username[params.player]

        for letter in params.letters:
            self._letters.remove(letter)
        player.fulfil_letters(params.letters)

    def event__game_init(self, params: GameInitParams) -> None:
        self._board = Board(params.board_settings)

        self._letters = list(params.letters)

        for username in params.players:
            player = Player(username=username)
            self._players_order.append(player)
            self._players_by_username[username] = player

    def event__game_start(self, params: GameStartParams) -> None:
        if params.player_to_start is None:
            self._player_idx_turn = 0
            return

        for idx, player in enumerate(self._players_order):
            if player.username == params.player_to_start:
                self._player_idx_turn = idx
                return

        raise ValueError('Unknown player to start')

    def event__player_move(self, params: PlayerMoveParams) -> None:
        assert self._player_idx_turn is not None

        player = self._players_by_username[params.player]
        if self._players_order[self._player_idx_turn] != player:
            raise ValueError('Player cannot do any moves now')

        played_letters = self._board.get_letters_to_insert_words(params.words)

        score = self._board.insert_words(params.words)
        player.add_score(score)
        if len(played_letters) == PLAYER_MAX_LETTERS:
            player.add_score(BONUS_FOR_ALL_LETTERS_USED)

        player.play_letters(played_letters + params.exchange_letters)

        self._player_idx_turn += 1
        self._player_idx_turn %= len(self._players_order)

    def get_player_score(self, player: str) -> int:
        return self._players_by_username[player].score
