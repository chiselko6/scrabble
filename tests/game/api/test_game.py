from datetime import datetime

import pytest

from scrabble.game import BoardSettings, BoardWord, Bonus, WordDirection
from scrabble.game.api import GameInitEvent, GameInitParams, GameStartEvent, GameStartParams
from scrabble.serializers.game.api import EventSchema


@pytest.mark.parametrize("game_id,players,letters,lang,width,height,init_word,bonuses", [
    (100, ["user1", "user2"], ['a', 'b', 'c', 'd'], "ru", 20, 40,
     BoardWord(word='qqq', start_x=3, start_y=4, direction=WordDirection.RIGHT),
     [Bonus(10, 10, 2)]),
    (1, ["user1", "user2", "user3"], [], "en", 10, 10,
     BoardWord(word='init_word', start_x=2, start_y=1, direction=WordDirection.DOWN),
     [Bonus(2, 2, 1), Bonus(3, 4, 4)]),
    (200, ["user1"], ['a', 'a', 'a'], "en", 100, 20, None, []),
])
def test_game_init_serializer(game_id, players, letters, lang, width, height, init_word, bonuses):
    timestamp = int(datetime.timestamp(datetime.now()))
    event = GameInitEvent(timestamp=timestamp,
                          sequence=1,
                          game_id=game_id,
                          params=GameInitParams(
                              players=players,
                              letters=letters,
                              lang=lang,
                              board_settings=BoardSettings(width=width, height=height,
                                                           init_word=init_word, bonuses=bonuses)
                          ))
    expected_dump = {"name": "GAME_INIT", "timestamp": timestamp, "sequence": 1, "game_id": game_id,
                     "params": {"players": players,
                                "letters": letters,
                                "lang": lang,
                                "board_settings": {"width": width, "height": height, "init_word": None, "bonuses": [
                                    {
                                        "location_x": bonus.location_x,
                                        "location_y": bonus.location_y,
                                        "multiplier": bonus.multiplier,
                                    }
                                    for bonus in bonuses
                                ]}}}
    if init_word is not None:
        expected_dump["params"]["board_settings"]["init_word"] = {
            "word": init_word.word,
            "start_x": init_word.start_x,
            "start_y": init_word.start_y,
            "direction": init_word.direction.name,
        }

    assert EventSchema().dump(event) == expected_dump
    assert EventSchema().load(expected_dump) == event


@pytest.mark.parametrize("player_to_start", [
    "user1", "user2", None,
])
def test_game_start_serializer(player_to_start):
    timestamp = int(datetime.timestamp(datetime.now()))
    event = GameStartEvent(timestamp=timestamp, sequence=2, game_id=2,
                           params=GameStartParams(player_to_start=player_to_start))
    expected_dump = {"name": "GAME_START", "timestamp": timestamp, "sequence": 2,
                     "game_id": 2, "params": {"player_to_start": player_to_start}}

    assert EventSchema().dump(event) == expected_dump
    assert EventSchema().load(expected_dump) == event

    expected_dump["params"].pop("player_to_start")
    event.params.player_to_start = None
    assert EventSchema().load(expected_dump) == event
