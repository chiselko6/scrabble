from copy import deepcopy

import marshmallow_dataclass
from marshmallow import Schema, fields
from marshmallow.exceptions import ValidationError

from scrabble.transport.msg import (AuthMessageRequest, AuthMessageRequestPayload, AuthMessageResponse,
                                    AuthMessageResponsePayload, MessageType, WebsocketMessage,
                                    WebsocketMessagePayload)

AuthMessageRequestPayloadSchema = marshmallow_dataclass.class_schema(AuthMessageRequestPayload)
AuthMessageRequestSchema = marshmallow_dataclass.class_schema(AuthMessageRequest)
AuthMessageResponsePayloadSchema = marshmallow_dataclass.class_schema(AuthMessageResponsePayload)
AuthMessageResponseSchema = marshmallow_dataclass.class_schema(AuthMessageResponse)
WebsocketMessagePayloadSchema = marshmallow_dataclass.class_schema(WebsocketMessagePayload)


class Enum(fields.Field):

    def __init__(self, choices, **kwargs):
        self._choices = choices
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, self._choices):
            raise ValidationError(f'{value} is not of type {self._choices}')

        return value.value

    def _deserialize(self, value, attr, data, **kwargs):
        if value not in self._choices._value2member_map_:
            raise ValidationError(f'{value} is not a member of {self._choices}')

        return self._choices._value2member_map_[value]


class MessageTypeSchema(Schema):
    type = Enum(choices=MessageType)


class WebsocketMessageSchema(Schema):
    payload = fields.Nested(WebsocketMessagePayloadSchema)

    def load(self, data) -> WebsocketMessage:
        data = deepcopy(data)
        msg_type = Enum(choices=MessageType).deserialize(data.pop('type'))

        if msg_type is None:
            raise ValidationError("'type' is a required attribute")

        if msg_type == MessageType.AUTH_REQUEST:
            return AuthMessageRequestSchema().load(data)
        elif msg_type == MessageType.AUTH_RESPONSE:
            return AuthMessageResponseSchema().load(data)
        else:
            return ValidationError(f'Unrecognized message type {msg_type}')

    def dump(self, obj) -> dict:
        if isinstance(obj, AuthMessageRequest):
            return {"type": MessageType.AUTH_REQUEST.value, **AuthMessageRequestSchema().dump(obj)}
        elif isinstance(obj, AuthMessageResponse):
            return {"type": MessageType.AUTH_RESPONSE.value, **AuthMessageResponseSchema().dump(obj)}
        else:
            raise ValidationError(f'Unrecognized object {obj}')
