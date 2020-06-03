from dataclasses import dataclass
from enum import Enum, unique

from scrabble.game.api import Event

from .msg import WebsocketMessage, WebsocketMessagePayload

__all__ = [
    'EventStatus',
    'EventMessagePayload',
    'EventMessage',
]


@unique
class EventStatus(Enum):
    REQUESTED = 'requested'
    APPROVED = 'approved'
    REJECTED = 'rejected'


@dataclass
class EventMessagePayload(WebsocketMessagePayload):
    event: Event


@dataclass
class EventMessage(WebsocketMessage):
    payload: EventMessagePayload
    status: EventStatus
