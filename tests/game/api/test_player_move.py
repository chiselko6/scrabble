from datetime import datetime

import pytest

from scrabble.game import BoardWord, WordDirection
from scrabble.game.api import PlayerMoveEvent, PlayerMoveParams
from scrabble.serializers.game.api import EventSchema


@pytest.mark.parametrize("username,words", [
    ("user1", [('word', 1, 1, WordDirection.RIGHT)]),
    ("user2", [('wordword', 10, 100, WordDirection.DOWN)]),
    ("user3", [('wordqu', 0, 220, WordDirection.RIGHT), ('anotherword', 20, 100, WordDirection.DOWN)]),
])
def test_player_move_serializer(username, words):
    timestamp = int(datetime.timestamp(datetime.now()))
    event = PlayerMoveEvent(timestamp=timestamp,
                            params=PlayerMoveParams(player=username, words=[
                                BoardWord(w[0], w[1], w[2], w[3])
                                for w in words
                            ]))
    expected_dump = {"name": "PLAYER_MOVE", "timestamp": timestamp,
                     "params": {"player": username, "words": [
                         {"word": w[0], "start_x": w[1], "start_y": w[2], "direction": w[3].name}
                         for w in words
                     ]}}

    assert EventSchema().dump(event) == expected_dump
    assert EventSchema().load(expected_dump) == event
