from dataclasses import dataclass, field
from typing import List, Optional

from scrabble.game.board import BoardSettings

from .base import Event, EventParams

__all__ = [
    'GameInitParams',
    'GameInitEvent',
    'GameStartParams',
    'GameStartEvent',
]


@dataclass
class GameInitParams(EventParams):
    players: List[str]
    board_settings: BoardSettings
    letters: List[str]


@dataclass
class GameInitEvent(Event):
    params: GameInitParams


@dataclass
class GameStartParams(EventParams):
    player_to_start: Optional[str] = field(default=None)


@dataclass
class GameStartEvent(Event):
    params: GameStartParams
