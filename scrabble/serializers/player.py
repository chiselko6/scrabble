from marshmallow_dataclass import class_schema

from scrabble.game import Player

__all__ = [
    'PlayerSchema',
]


PlayerSchema = class_schema(Player)
