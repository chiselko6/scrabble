from dataclasses import dataclass

__all__ = [
    'WebsocketMessagePayload',
    'WebsocketMessage',
    'AuthMessageRequestPayload',
    'AuthMessageResponsePayload',
    'AuthMessageRequest',
    'AuthMessageResponse',
    'NewConnectionPayload',
    'NewConnectionMessage',
    'EndConnectionPayload',
    'EndConnectionMessage',
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
    game_id: int


@dataclass
class AuthMessageResponsePayload(WebsocketMessagePayload):
    ok: bool


@dataclass
class AuthMessageRequest(WebsocketMessage):
    payload: AuthMessageRequestPayload


@dataclass
class AuthMessageResponse(WebsocketMessage):
    payload: AuthMessageResponsePayload


@dataclass
class NewConnectionPayload(WebsocketMessagePayload):
    username: str


@dataclass
class NewConnectionMessage(WebsocketMessage):
    payload: NewConnectionPayload


@dataclass
class EndConnectionPayload(WebsocketMessagePayload):
    username: str


@dataclass
class EndConnectionMessage(WebsocketMessage):
    payload: EndConnectionPayload
