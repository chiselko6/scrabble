from dataclasses import dataclass
from typing import List

from .base import Event


@dataclass
class PlayerAddLettersParams:
    player: str
    letters: List[str]


class PlayerAddLettersEvent(Event):
    params: PlayerAddLettersParams


@dataclass
class PlayerScoreParams:
    player: str
    score: int


class PlayerScoreEvent(Event):
    params: PlayerScoreParams
