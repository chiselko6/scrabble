from datetime import datetime

import pytest

from scrabble.game import BoardSettings, Bonus
from scrabble.game.api import GameInitEvent, GameInitParams, GameStartEvent, GameStartParams
from scrabble.serializers.game.api import EventSchema


@pytest.mark.parametrize("players,width,height,bonuces", [
    (["user1", "user2"], 20, 40, [Bonus(10, 10, 2)]),
    (["user1", "user2", "user3"], 10, 10, [Bonus(2, 2, 1), Bonus(3, 4, 4)]),
    (["user1"], 100, 20, []),
])
def test_game_init_serializer(players, width, height, bonuces):
    timestamp = int(datetime.timestamp(datetime.now()))
    event = GameInitEvent(timestamp=timestamp,
                          params=GameInitParams(
                              players=players,
                              board_settings=BoardSettings(width=width, height=height, bonuces=bonuces)
                          ))
    expected_dump = {"name": "GAME_INIT", "timestamp": timestamp,
                     "params": {"players": players,
                                "board_settings": {"width": width, "height": height, "bonuces": [
                                    {
                                        "location_x": bonus.location_x,
                                        "location_y": bonus.location_y,
                                        "multiplier": bonus.multiplier,
                                    }
                                    for bonus in bonuces
                                ]}}}

    assert EventSchema().dump(event) == expected_dump
    assert EventSchema().load(expected_dump) == event


@pytest.mark.parametrize("player_to_start", [
    "user1", "user2", None,
])
def test_game_start_serializer(player_to_start):
    timestamp = int(datetime.timestamp(datetime.now()))
    event = GameStartEvent(timestamp=timestamp,
                           params=GameStartParams(player_to_start=player_to_start))
    expected_dump = {"name": "GAME_START", "timestamp": timestamp,
                     "params": {"player_to_start": player_to_start}}

    assert EventSchema().dump(event) == expected_dump
    assert EventSchema().load(expected_dump) == event

    expected_dump["params"].pop("player_to_start")
    event.params.player_to_start = None
    assert EventSchema().load(expected_dump) == event
