from dataclasses import dataclass, field
from enum import Enum, unique


@unique
class MessageType(Enum):
    AUTH_REQUEST = 'auth_request'
    AUTH_RESPONSE = 'auth_response'


@dataclass
class WebsocketMessagePayload:
    ...


@dataclass
class WebsocketMessage:
    payload: WebsocketMessagePayload = field(default_factory=WebsocketMessagePayload)


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
