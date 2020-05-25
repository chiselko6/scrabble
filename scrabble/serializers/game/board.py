from marshmallow_dataclass import class_schema

from scrabble.game import BoardSettings, Bonus

__all__ = [
    'BoardSettingsSchema',
    'BonusSchema',
]


BoardSettingsSchema = class_schema(BoardSettings)
BonusSchema = class_schema(Bonus)
