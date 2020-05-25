from dataclasses import dataclass

__all__ = [
    'WebsocketMessagePayload',
    'WebsocketMessage',
    'AuthMessageRequestPayload',
    'AuthMessageResponsePayload',
    'AuthMessageRequest',
    'AuthMessageResponse',
]


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
