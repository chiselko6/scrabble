from operator import methodcaller
from typing import Iterable, List, MutableMapping, MutableSet, Optional

from .api import (Event, GameInitEvent, GameInitParams, GameStartEvent, GameStartParams, PlayerAddLettersEvent,
                  PlayerAddLettersParams, PlayerMoveEvent, PlayerMoveParams)
from .board import Board
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

    def __init__(self, *, events: Optional[Iterable[Event]] = None):
        self._players_order: List[Player] = []
        self._players_by_username: MutableMapping[str, Player] = {}
        self._players_connected: MutableSet[str] = set()
        self._player_idx_turn: Optional[int] = None
        self._board: Optional[Board] = None

        if events:
            for event in events:
                self.apply_event(event)

    def apply_event(self, event: Event) -> None:
        if type(event) in self.EVENT_MAP:
            methodcaller(self, f'event__{self.EVENT_MAP[type(event)]}')
        else:
            raise ValueError(f'Unknown event {event}')

    def event__player_add_letters(self, params: PlayerAddLettersParams) -> None:
        player = self._players_by_username[params.player]

        player.add_letters(params.letters)

    def event__game_init(self, params: GameInitParams) -> None:
        self._board = Board(params.board_settings)
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
        player = self._players_by_username[params.player]
        if self._players_order[self._player_idx_turn] != player:
            raise ValueError('Player cannot do any moves now')

        score = 0

        for word_move in params.words:
            score += self._board.insert_word(word_move)
        player.add_score(score)
        self._player_idx_turn += 1
        self._player_idx_turn %= len(self._players_order)

    def connect_player(self, player_username) -> None:
        self._players_connected.add(player_username)

    def disconnect_player(self, player_username) -> None:
        self._players_connected.remove(player_username)
