from marshmallow_dataclass import class_schema

from scrabble.game.api import GameInitEvent, GameInitParams, GameStartEvent, GameStartParams

__all__ = [
    'GameInitEventSchema',
    'GameInitParamsSchema',
    'GameStartEventSchema',
    'GameStartParamsSchema',
]


GameInitEventSchema = class_schema(GameInitEvent)
GameInitParamsSchema = class_schema(GameInitParams)
GameStartEventSchema = class_schema(GameStartEvent)
GameStartParamsSchema = class_schema(GameStartParams)
