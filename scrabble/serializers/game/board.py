from marshmallow_dataclass import class_schema

from scrabble.game import BoardSettings, Bonus

BoardSettingsSchema = class_schema(BoardSettings)
BonusSchema = class_schema(Bonus)
