from marshmallow_dataclass import class_schema

from scrabble.game.api import PlayerAddLettersEvent, PlayerAddLettersParams

__all__ = [
    'PlayerAddLettersEventSchema',
    'PlayerAddLettersParamsSchema',
]


PlayerAddLettersEventSchema = class_schema(PlayerAddLettersEvent)
PlayerAddLettersParamsSchema = class_schema(PlayerAddLettersParams)
