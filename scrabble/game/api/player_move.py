from dataclasses import dataclass
from typing import List

from scrabble.game.board import BoardWord

from .base import Event


@dataclass
class PlayerMoveParams:
    player: str
    words: List[BoardWord]


class PlayerMoveEvent(Event):
    params: PlayerMoveParams
