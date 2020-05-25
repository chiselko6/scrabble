from dataclasses import dataclass
from enum import Enum, unique

__all__ = [
    'MessageType',
    'WebsocketMessagePayload',
    'WebsocketMessage',
    'AuthMessageRequestPayload',
    'AuthMessageResponsePayload',
    'AuthMessageRequest',
    'AuthMessageResponse',
]


@unique
class MessageType(Enum):
    AUTH_REQUEST = 'auth_request'
    AUTH_RESPONSE = 'auth_response'


@dataclass
class WebsocketMessagePayload:
    ...


@dataclass
class WebsocketMessage:
    payload: WebsocketMessagePayload


@dataclass
class AuthMessageRequestPayload(WebsocketMessagePayload):
    username: str


@dataclass
class AuthMessageResponsePayload(WebsocketMessagePayload):
    ok: bool


@dataclass
class AuthMessageRequest(WebsocketMessage):
    payload: AuthMessageRequestPayload


@dataclass
class AuthMessageResponse(WebsocketMessage):
    payload: AuthMessageResponsePayload
