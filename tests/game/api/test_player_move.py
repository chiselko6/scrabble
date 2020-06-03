import string
from datetime import datetime

import pytest

from scrabble.game import BoardWord, BoardWords, WordDirection
from scrabble.game.api import PlayerMoveEvent, PlayerMoveParams
from scrabble.serializers.game.api import EventSchema


@pytest.mark.parametrize("username,words,exchange_letters", [
    ("user1", [('word', 1, 1, WordDirection.RIGHT)], ['a', 'b', 'c']),
    ("user2", [('wordword', 10, 100, WordDirection.DOWN)], []),
    ("user3", [('wordqu', 0, 220, WordDirection.RIGHT), ('anotherword', 20, 100, WordDirection.DOWN)],
     list(string.ascii_lowercase)),
])
def test_player_move_serializer(username, words, exchange_letters):
    timestamp = int(datetime.timestamp(datetime.now()))
    event = PlayerMoveEvent(timestamp=timestamp, sequence=4,
                            params=PlayerMoveParams(player=username, words=BoardWords(words=[
                                BoardWord(w[0], w[1], w[2], w[3])
                                for w in words
                            ]), exchange_letters=exchange_letters))
    expected_dump = {"name": "PLAYER_MOVE", "timestamp": timestamp, "sequence": 4,
                     "params": {"player": username, "words": {"words": [
                         {"word": w[0], "start_x": w[1], "start_y": w[2], "direction": w[3].name}
                         for w in words
                     ]}, "exchange_letters": exchange_letters}}

    assert EventSchema().dump(event) == expected_dump
    assert EventSchema().load(expected_dump) == event
