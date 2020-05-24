import marshmallow_dataclass

from scrabble.game import Player

PlayerSchema = marshmallow_dataclass.class_schema(Player)
