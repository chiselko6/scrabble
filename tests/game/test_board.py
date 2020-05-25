import pytest

from scrabble.game import Board, BoardSettings, BoardWord, Bonus, WordDirection
from scrabble.serializers.game import BoardSettingsSchema, BonusSchema


@pytest.mark.parametrize("x,y,multiplier", [(0, 0, 2), (10, 20, 4), (3, 2, 0)])
def test_bonus_serializer(x, y, multiplier):
    bonus = Bonus(location_x=x, location_y=y, multiplier=multiplier)
    dumped = BonusSchema().dump(bonus)
    assert dumped == {"location_x": x, "location_y": y, "multiplier": multiplier}
    assert bonus == BonusSchema().load(dumped)


def test_bonus_invalid():
    with pytest.raises(ValueError):
        Bonus(location_x=-2, location_y=0, multiplier=2)


@pytest.mark.parametrize("width,height,bonuces", [
    (20, 20, []), (10, 20, [Bonus(location_x=5, location_y=6, multiplier=2)])
])
def test_board_settings_serializer(width, height, bonuces):
    settings = BoardSettings(width=width, height=height, bonuces=bonuces)
    expected_dump = {
        "width": width,
        "height": height,
        "bonuces": [
            {"location_x": b.location_x, "location_y": b.location_y, "multiplier": b.multiplier}
            for b in bonuces
        ]
    }
    assert BoardSettingsSchema().dump(settings) == expected_dump
    assert settings == BoardSettingsSchema().load(expected_dump)


def test_board_settings_invalid():
    with pytest.raises(ValueError):
        BoardSettings(width=2, height=20)

    with pytest.raises(ValueError):
        BoardSettings(width=30, height=9)

    with pytest.raises(ValueError):
        BoardSettings(width=30, height=30, bonuces=[Bonus(location_x=20, location_y=35, multiplier=2)])


def test_board_insert_words():
    board = Board(settings=BoardSettings(width=100, height=100))

    assert board.insert_word(BoardWord('abacaba', 10, 10, WordDirection.RIGHT)) == 7

    with pytest.raises(ValueError):
        board.insert_word(BoardWord('qqqqq', 10, 10, WordDirection.DOWN))

    with pytest.raises(ValueError):
        board.insert_word(BoardWord('abracadabra', 10, 10, WordDirection.RIGHT))

    assert board.insert_word(BoardWord('abracadabra', 10, 10, WordDirection.DOWN)) == 11
    assert board.insert_word(BoardWord('raise', 10, 12, WordDirection.RIGHT)) == 5
    assert board.insert_word(BoardWord('custom', 13, 10, WordDirection.DOWN)) == 6


def test_board_insert_words_invalid():
    board = Board(settings=BoardSettings(width=100, height=100))

    with pytest.raises(ValueError):
        board.insert_word(BoardWord('wordwordword', 90, 90, WordDirection.RIGHT))
    with pytest.raises(ValueError):
        board.insert_word(BoardWord('wordwordword', 90, 90, WordDirection.DOWN))


def test_board_insert_words_bonuces():
    board = Board(settings=BoardSettings(width=100, height=100, bonuces=[
        Bonus(location_x=10, location_y=10, multiplier=2), Bonus(location_x=12, location_y=10, multiplier=3)
    ]))

    assert board.insert_word(BoardWord('abacaba', 10, 10, WordDirection.DOWN)) == 7 * 2
    assert board.insert_word(BoardWord('abracadabra', 10, 10, WordDirection.RIGHT)) == 11 * (2 + 3)


@pytest.mark.parametrize("w1,w2,overlaps,intersects", [
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 0, 0, WordDirection.RIGHT), True, False),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 4, 0, WordDirection.RIGHT), True, False),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 2, 0, WordDirection.RIGHT), True, False),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 5, 0, WordDirection.RIGHT), False, False),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 1, 1, WordDirection.RIGHT), True, False),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 2, 10, WordDirection.RIGHT), False, False),

    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 0, 0, WordDirection.DOWN), False, True),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 1, 0, WordDirection.DOWN), False, True),
    (BoardWord('word', 3, 3, WordDirection.RIGHT), BoardWord('word', 3, 1, WordDirection.DOWN), False, True),
    (BoardWord('word', 3, 3, WordDirection.RIGHT), BoardWord('word', 3, 4, WordDirection.DOWN), True, False),
    (BoardWord('word', 1, 1, WordDirection.RIGHT), BoardWord('word', 5, 0, WordDirection.DOWN), True, False),
    (BoardWord('word', 1, 1, WordDirection.RIGHT), BoardWord('word', 0, 1, WordDirection.DOWN), True, False),
])
def test_board_words(w1: BoardWord, w2: BoardWord, overlaps: bool, intersects: bool):
    assert w1.overlaps(w2) == overlaps
    assert w2.overlaps(w1) == overlaps
    assert w1.intersects(w2) == intersects
    assert w2.intersects(w1) == intersects


@pytest.mark.parametrize("word,path", [
    (BoardWord('word', 0, 0, WordDirection.RIGHT), [(i, 0) for i in range(4)]),
    (BoardWord('word', 5, 2, WordDirection.RIGHT), [(i, 2) for i in range(5, 9)]),
    (BoardWord('wordword', 0, 0, WordDirection.RIGHT), [(i, 0) for i in range(8)]),
    (BoardWord('word', 0, 0, WordDirection.DOWN), [(0, i) for i in range(4)]),
    (BoardWord('word', 10, 20, WordDirection.DOWN), [(10, i) for i in range(20, 24)]),
    (BoardWord('wordword', 5, 6, WordDirection.DOWN), [(5, i) for i in range(6, 14)]),
    (BoardWord('word', 5, 5, WordDirection.RIGHT), [(i, 5) for i in range(5, 9)]),
    (BoardWord('word', 7, 3, WordDirection.DOWN), [(7, i) for i in range(3, 7)]),
])
def test_board_word_path(word, path):
    assert word.path == path


@pytest.mark.parametrize("w1,w2,point", [
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 0, 0, WordDirection.DOWN), (0, 0)),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 0, 0, WordDirection.RIGHT), None),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 3, 0, WordDirection.DOWN), (3, 0)),
    (BoardWord('word', 5, 5, WordDirection.RIGHT), BoardWord('word', 5, 3, WordDirection.DOWN), (5, 5)),
    (BoardWord('word', 5, 5, WordDirection.RIGHT), BoardWord('word', 7, 3, WordDirection.DOWN), (7, 5)),
])
def test_board_word_intersection(w1, w2, point):
    assert w1.intersection(w2) == point
    assert w2.intersection(w1) == point


@pytest.mark.parametrize("word,x,y,letter", [
    (BoardWord("word", 5, 7, WordDirection.RIGHT), 5, 7, 'w'),
    (BoardWord("word", 5, 7, WordDirection.RIGHT), 7, 7, 'r'),
    (BoardWord("word", 5, 7, WordDirection.RIGHT), 8, 7, 'd'),
    (BoardWord("word", 5, 7, WordDirection.RIGHT), 9, 7, None),
    (BoardWord("word", 5, 7, WordDirection.RIGHT), 4, 7, None),
    (BoardWord("word", 5, 7, WordDirection.RIGHT), 5, 8, None),
    (BoardWord("word", 5, 7, WordDirection.DOWN), 5, 7, 'w'),
    (BoardWord("word", 5, 7, WordDirection.DOWN), 5, 8, 'o'),
    (BoardWord("word", 5, 7, WordDirection.DOWN), 5, 10, 'd'),
    (BoardWord("word", 5, 7, WordDirection.DOWN), 4, 8, None),
    (BoardWord("word", 5, 7, WordDirection.DOWN), 5, 11, None),
])
def test_letter_at(word: BoardWord, x: int, y: int, letter: str):
    assert word.letter_at(x, y) == letter
