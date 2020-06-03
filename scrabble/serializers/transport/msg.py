from copy import deepcopy

import marshmallow_dataclass
from marshmallow import Schema, fields
from marshmallow.exceptions import ValidationError
from marshmallow_enum import EnumField

from scrabble.transport import (AuthMessageRequest, AuthMessageRequestPayload, AuthMessageResponse,
                                AuthMessageResponsePayload, EndConnectionMessage, EndConnectionPayload, EventMessage,
                                MessageType, NewConnectionMessage, NewConnectionPayload, WebsocketMessage,
                                WebsocketMessagePayload)

from .event import EventMessageSchema

__all__ = [
    'AuthMessageRequestPayloadSchema',
    'AuthMessageRequestSchema',
    'AuthMessageResponsePayloadSchema',
    'AuthMessageResponseSchema',
    'NewConnectionPayloadSchema',
    'NewConnectionMessageSchema',
    'EndConnectionPayloadSchema',
    'EndConnectionMessageSchema',
    'WebsocketMessagePayloadSchema',
    'WebsocketMessageSchema',
]


AuthMessageRequestPayloadSchema = marshmallow_dataclass.class_schema(AuthMessageRequestPayload)
AuthMessageRequestSchema = marshmallow_dataclass.class_schema(AuthMessageRequest)
AuthMessageResponsePayloadSchema = marshmallow_dataclass.class_schema(AuthMessageResponsePayload)
AuthMessageResponseSchema = marshmallow_dataclass.class_schema(AuthMessageResponse)
NewConnectionPayloadSchema = marshmallow_dataclass.class_schema(NewConnectionPayload)
NewConnectionMessageSchema = marshmallow_dataclass.class_schema(NewConnectionMessage)
EndConnectionPayloadSchema = marshmallow_dataclass.class_schema(EndConnectionPayload)
EndConnectionMessageSchema = marshmallow_dataclass.class_schema(EndConnectionMessage)
WebsocketMessagePayloadSchema = marshmallow_dataclass.class_schema(WebsocketMessagePayload)


class WebsocketMessageSchema(Schema):
    payload = fields.Nested(WebsocketMessagePayloadSchema)

    MESSAGE_SCHEMA_MAP = {
        MessageType.AUTH_REQUEST: AuthMessageRequestSchema,
        MessageType.AUTH_RESPONSE: AuthMessageResponseSchema,
        MessageType.NEW_CONNECTION: NewConnectionMessageSchema,
        MessageType.END_CONNECTION: EndConnectionMessageSchema,
        MessageType.EVENT: EventMessageSchema,
    }
    MESSAGE_TYPE_MAP = {
        AuthMessageRequest: MessageType.AUTH_REQUEST,
        AuthMessageResponse: MessageType.AUTH_RESPONSE,
        NewConnectionMessage: MessageType.NEW_CONNECTION,
        EndConnectionMessage: MessageType.END_CONNECTION,
        EventMessage: MessageType.EVENT,
    }

    def load(self, data, **kwargs) -> WebsocketMessage:
        data = deepcopy(data)
        msg_type = EnumField(MessageType).deserialize(data.pop('type'))

        if msg_type is None:
            raise ValidationError("'type' is a required attribute")

        if msg_type not in self.MESSAGE_SCHEMA_MAP:
            raise ValidationError(f'Unrecognized message type {msg_type}')

        schema = self.MESSAGE_SCHEMA_MAP[msg_type]
        return schema().load(data, **kwargs)

    def dump(self, obj, **kwargs) -> dict:
        if type(obj) not in self.MESSAGE_TYPE_MAP:
            raise ValidationError(f'Unrecognized object {obj}')

        obj_type = self.MESSAGE_TYPE_MAP[type(obj)]
        schema = self.MESSAGE_SCHEMA_MAP[obj_type]
        return {"type": obj_type.name, **schema().dump(obj, **kwargs)}
