from marshmallow_dataclass import class_schema

from scrabble.game import BoardSettings, BoardWord, BoardWords, Bonus

__all__ = [
    'BoardSettingsSchema',
    'BonusSchema',
    'BoardWordSchema',
    'BoardWordsSchema',
]


BoardSettingsSchema = class_schema(BoardSettings)
BonusSchema = class_schema(Bonus)
BoardWordSchema = class_schema(BoardWord)
BoardWordsSchema = class_schema(BoardWords)
