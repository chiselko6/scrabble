from dataclasses import dataclass
from enum import Enum, unique

__all__ = [
    'EventName',
    'EventParams',
    'Event',
]


@unique
class EventName(Enum):
    PLAYER_ADD_LETTERS = 'player_add_letters'
    GAME_INIT = 'game_init'
    GAME_START = 'game_start'
    PLAYER_MOVE = 'player_move'


@dataclass
class EventParams:
    ...


@dataclass
class Event:
    timestamp: int
    params: EventParams
