from dataclasses import dataclass
from typing import List

from scrabble.game.board import BoardWord

from .base import Event, EventParams

__all__ = [
    'PlayerMoveParams',
    'PlayerMoveEvent',
]


@dataclass
class PlayerMoveParams(EventParams):
    player: str
    words: List[BoardWord]


@dataclass
class PlayerMoveEvent(Event):
    params: PlayerMoveParams
