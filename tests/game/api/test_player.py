from datetime import datetime

import pytest

from scrabble.game.api import PlayerAddLettersEvent, PlayerAddLettersParams
from scrabble.serializers.game.api import EventSchema


@pytest.mark.parametrize("username,letters", [
    ("user1", ["a", "b", "c"]),
    ("user2", []),
    ("user3", ["a", "a", "a"]),
])
def test_player_add_letters_serializer(username, letters):
    timestamp = int(datetime.timestamp(datetime.now()))
    event = PlayerAddLettersEvent(timestamp=timestamp,
                                  params=PlayerAddLettersParams(player=username, letters=letters))
    expected_dump = {"name": "PLAYER_ADD_LETTERS", "timestamp": timestamp,
                     "params": {"player": username, "letters": letters}}

    assert EventSchema().dump(event) == expected_dump
    assert EventSchema().load(expected_dump) == event
