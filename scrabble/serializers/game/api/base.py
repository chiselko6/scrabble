from copy import deepcopy

from marshmallow import Schema, fields
from marshmallow.exceptions import ValidationError
from marshmallow_dataclass import class_schema
from marshmallow_enum import EnumField

from scrabble.game.api import (Event, EventName, EventParams, GameInitEvent, GameStartEvent, PlayerAddLettersEvent,
                               PlayerMoveEvent)

from .game import GameInitEventSchema, GameStartEventSchema
from .player import PlayerAddLettersEventSchema
from .player_move import PlayerMoveEventSchema

__all__ = [
    'EventParamsSchema',
    'EventSchema',
]


EventParamsSchema = class_schema(EventParams)


class EventSchema(Schema):
    timestamp = fields.Integer()
    payload = fields.Nested(EventParamsSchema)

    EVENT_NAME_SCHEMA_MAP = {
        EventName.PLAYER_ADD_LETTERS: PlayerAddLettersEventSchema,
        EventName.PLAYER_MOVE: PlayerMoveEventSchema,
        EventName.GAME_INIT: GameInitEventSchema,
        EventName.GAME_START: GameStartEventSchema,
    }
    EVENT_TYPE_NAME_MAP = {
        PlayerAddLettersEvent: EventName.PLAYER_ADD_LETTERS,
        PlayerMoveEvent: EventName.PLAYER_MOVE,
        GameInitEvent: EventName.GAME_INIT,
        GameStartEvent: EventName.GAME_START,
    }

    def load(self, data, **kwargs) -> Event:
        data = deepcopy(data)
        event_name = EnumField(EventName).deserialize(data.pop('name'))

        if event_name is None:
            raise ValidationError('"name" is a required attribute')

        if event_name not in self.EVENT_NAME_SCHEMA_MAP:
            raise ValidationError(f"Couldn't find event name {event_name}")

        schema = self.EVENT_NAME_SCHEMA_MAP[event_name]
        return schema().load(data, **kwargs)

    def dump(self, obj, **kwargs) -> dict:
        if type(obj) not in self.EVENT_TYPE_NAME_MAP:
            raise ValidationError(f'Unrecognized object type {type(obj)}')

        event_name = self.EVENT_TYPE_NAME_MAP[type(obj)]
        schema = self.EVENT_NAME_SCHEMA_MAP[event_name]
        return {"name": event_name.name, **schema().dump(obj, **kwargs)}
