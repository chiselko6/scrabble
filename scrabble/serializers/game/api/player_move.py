from marshmallow_dataclass import class_schema

from scrabble.game.api import PlayerMoveEvent, PlayerMoveParams

__all__ = [
    'PlayerMoveEventSchema',
    'PlayerMoveParamsSchema',
]


PlayerMoveEventSchema = class_schema(PlayerMoveEvent)
PlayerMoveParamsSchema = class_schema(PlayerMoveParams)
