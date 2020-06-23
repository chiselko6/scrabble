from dataclasses import dataclass
from typing import List

from .base import Event, EventParams

__all__ = [
    'PlayerAddLettersParams',
    'PlayerAddLettersEvent',
]


@dataclass
class PlayerAddLettersParams(EventParams):
    player: str
    letters: List[str]


@dataclass
class PlayerAddLettersEvent(Event):
    params: PlayerAddLettersParams
