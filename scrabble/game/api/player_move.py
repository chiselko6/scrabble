from dataclasses import dataclass
from typing import List

from scrabble.game.board import BoardWords

from .base import Event, EventParams

__all__ = [
    'PlayerMoveParams',
    'PlayerMoveEvent',
]


@dataclass
class PlayerMoveParams(EventParams):
    player: str
    words: BoardWords
    exchange_letters: List[str]


@dataclass
class PlayerMoveEvent(Event):
    params: PlayerMoveParams
