from copy import deepcopy

import marshmallow_dataclass
from marshmallow import Schema, fields
from marshmallow.exceptions import ValidationError
from marshmallow_enum import EnumField

from scrabble.transport.msg import (AuthMessageRequest, AuthMessageRequestPayload, AuthMessageResponse,
                                    AuthMessageResponsePayload, MessageType, WebsocketMessage, WebsocketMessagePayload)

AuthMessageRequestPayloadSchema = marshmallow_dataclass.class_schema(AuthMessageRequestPayload)
AuthMessageRequestSchema = marshmallow_dataclass.class_schema(AuthMessageRequest)
AuthMessageResponsePayloadSchema = marshmallow_dataclass.class_schema(AuthMessageResponsePayload)
AuthMessageResponseSchema = marshmallow_dataclass.class_schema(AuthMessageResponse)
WebsocketMessagePayloadSchema = marshmallow_dataclass.class_schema(WebsocketMessagePayload)


class WebsocketMessageSchema(Schema):
    payload = fields.Nested(WebsocketMessagePayloadSchema)

    MESSAGE_SCHEMA_MAP = {
        MessageType.AUTH_REQUEST: AuthMessageRequestSchema,
        MessageType.AUTH_RESPONSE: AuthMessageResponseSchema,
    }
    MESSAGE_TYPE_MAP = {
        AuthMessageRequest: MessageType.AUTH_REQUEST,
        AuthMessageResponse: MessageType.AUTH_RESPONSE,
    }

    def load(self, data) -> WebsocketMessage:
        data = deepcopy(data)
        msg_type = EnumField(MessageType).deserialize(data.pop('type'))

        if msg_type is None:
            raise ValidationError("'type' is a required attribute")

        if msg_type not in self.MESSAGE_SCHEMA_MAP:
            raise ValidationError(f'Unrecognized message type {msg_type}')

        schema = self.MESSAGE_SCHEMA_MAP[msg_type]
        return schema().load(data)

    def dump(self, obj) -> dict:
        if type(obj) not in self.MESSAGE_TYPE_MAP:
            raise ValidationError(f'Unrecognized object {obj}')

        obj_type = self.MESSAGE_TYPE_MAP[type(obj)]
        schema = self.MESSAGE_SCHEMA_MAP[obj_type]
        return {"type": obj_type.name, **schema().dump(obj)}
