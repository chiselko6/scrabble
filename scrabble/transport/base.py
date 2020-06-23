from enum import Enum, unique

__all__ = [
    'MessageType',
]


@unique
class MessageType(Enum):
    AUTH_REQUEST = 'auth_request'
    AUTH_RESPONSE = 'auth_response'
    NEW_CONNECTION = 'new_connection'
    END_CONNECTION = 'end_connection'
    EVENT = 'event'
