from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

from scrabble.serializers.game.api import EventSchema
from scrabble.transport import EventMessage, EventMessagePayload, EventStatus

__all__ = [
    'EventMessagePayloadSchema',
    'EventMessageSchema',
]


class EventMessagePayloadSchema(Schema):
    event = fields.Nested(EventSchema)
    status = EnumField(EventStatus)

    @post_load
    def make(self, data, **kwargs) -> EventMessagePayload:
        return EventMessagePayload(**data)


class EventMessageSchema(Schema):
    payload = fields.Nested(EventMessagePayloadSchema)

    @post_load
    def make(self, data, **kwargs) -> EventMessage:
        return EventMessage(**data)
