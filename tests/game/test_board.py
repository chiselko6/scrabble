import pytest

from scrabble.game import Board, BoardSettings, BoardWord, BoardWords, Bonus, WordDirection
from scrabble.game.exceptions import WordIntersectionError
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


@pytest.mark.parametrize("width,height,init_word,bonuses", [
    (20, 20, BoardWord('abacaba', 5, 5, WordDirection.RIGHT), []),
    (10, 20, BoardWord('word', 3, 3, WordDirection.DOWN), [Bonus(location_x=5, location_y=6, multiplier=2)]),
    (30, 40, BoardWord('qqqq', 20, 30, WordDirection.DOWN), [Bonus(location_x=5, location_y=6, multiplier=2)]),
    (50, 50, None, [Bonus(location_x=5, location_y=6, multiplier=2)]),
])
def test_board_settings_serializer(width, height, init_word, bonuses):
    settings = BoardSettings(width=width, height=height, init_word=init_word, bonuses=bonuses)
    expected_dump = {
        "width": width,
        "height": height,
        "bonuses": [
            {"location_x": b.location_x, "location_y": b.location_y, "multiplier": b.multiplier}
            for b in bonuses
        ]
    }
    if init_word is not None:
        expected_dump["init_word"] = {"word": init_word.word,
                                      "start_x": init_word.start_x,
                                      "start_y": init_word.start_y,
                                      "direction": init_word.direction.name}
    else:
        expected_dump["init_word"] = None
    assert BoardSettingsSchema().dump(settings) == expected_dump
    assert settings == BoardSettingsSchema().load(expected_dump)


def test_board_settings_invalid():
    with pytest.raises(ValueError):
        BoardSettings(width=2, height=20)

    with pytest.raises(ValueError):
        BoardSettings(width=30, height=9)

    with pytest.raises(ValueError):
        BoardSettings(width=30, height=30, bonuses=[Bonus(location_x=20, location_y=35, multiplier=2)])

    with pytest.raises(ValueError):
        BoardSettings(width=30, height=40,
                      init_word=BoardWord(word='longlongword', start_x=20, start_y=0, direction=WordDirection.RIGHT))

    with pytest.raises(ValueError):
        BoardSettings(width=30, height=40,
                      init_word=BoardWord(word='longlongword', start_x=0, start_y=30, direction=WordDirection.DOWN))


def test_board_insert_word():
    board = Board(settings=BoardSettings(width=100, height=100))

    assert board.insert_word(BoardWord('abacaba', 10, 10, WordDirection.RIGHT)) == 7

    with pytest.raises(WordIntersectionError):
        board.insert_word(BoardWord('qqqqq', 10, 10, WordDirection.DOWN))

    with pytest.raises(WordIntersectionError):
        board.insert_word(BoardWord('abracadabra', 10, 10, WordDirection.RIGHT))

    assert board.insert_word(BoardWord('abracadabra', 10, 10, WordDirection.DOWN)) == 11
    assert board.insert_word(BoardWord('raise', 10, 12, WordDirection.RIGHT)) == 5
    assert board.insert_word(BoardWord('custom', 13, 10, WordDirection.DOWN)) == 6


@pytest.mark.parametrize("words,position,letter", [
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('star', 0, 1, WordDirection.RIGHT),
                       BoardWord('ship', 0, 2, WordDirection.RIGHT)]), (0, 1), 's'),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('star', 0, 1, WordDirection.RIGHT),
                       BoardWord('ship', 0, 2, WordDirection.RIGHT)]), (1, 2), 'h'),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('star', 0, 1, WordDirection.RIGHT),
                       BoardWord('ship', 0, 2, WordDirection.RIGHT)]), (4, 1), None),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('star', 0, 1, WordDirection.RIGHT),
                       BoardWord('ship', 0, 2, WordDirection.RIGHT)]), (1, 4), None),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('star', 0, 1, WordDirection.RIGHT),
                       BoardWord('ship', 0, 2, WordDirection.RIGHT)]), (0, 0), 'w'),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('star', 0, 1, WordDirection.RIGHT),
                       BoardWord('ship', 0, 2, WordDirection.RIGHT)]), (3, 0), 'd'),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('star', 0, 1, WordDirection.RIGHT),
                       BoardWord('ship', 0, 2, WordDirection.RIGHT)]), (0, 3), None),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('wiki', 0, 0, WordDirection.DOWN)]), (0, 0), 'w'),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('wiki', 0, 0, WordDirection.DOWN)]), (1, 1), None),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('wiki', 0, 0, WordDirection.DOWN)]), (2, 0), 'r'),
    (BoardWords(words=[BoardWord('word', 0, 0, WordDirection.RIGHT),
                       BoardWord('wiki', 0, 0, WordDirection.DOWN)]), (0, 3), 'i'),
])
def test_board_words_letter_at(words, position, letter):
    assert words.letter_at(position[0], position[1]) == letter


@pytest.mark.parametrize("words,position", [
    ([BoardWord('word', 0, 0, WordDirection.RIGHT),
      BoardWord('star', 0, 0, WordDirection.DOWN),
      BoardWord('ship', 0, 2, WordDirection.RIGHT)], (0, 1)),
    ([BoardWord('word', 0, 0, WordDirection.RIGHT),
      BoardWord('star', 0, 0, WordDirection.RIGHT)], (1, 2)),
    ([BoardWord('word', 0, 0, WordDirection.RIGHT),
      BoardWord('star', 0, 0, WordDirection.RIGHT),
      BoardWord('ship', 0, 0, WordDirection.DOWN)], (4, 1)),
])
def test_board_words_letter_at_invalid(words, position):
    with pytest.raises(WordIntersectionError):
        BoardWords(words=words)


@pytest.mark.parametrize("init_word,words,score", [
    (None, BoardWords(words=[BoardWord('abacaba', 10, 10, WordDirection.RIGHT)]), 7),
    (None, BoardWords(words=[BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
                             BoardWord('abracadabra', 10, 10, WordDirection.DOWN)]), 7+11),
    (None, BoardWords(words=[BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
                             BoardWord('abracadabra', 10, 10, WordDirection.DOWN),
                             BoardWord('ababahalamaha', 6, 13, WordDirection.RIGHT)]), 7+11+13),
    (BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
     BoardWords(words=[BoardWord('abacaba', 12, 8, WordDirection.DOWN),
                       BoardWord('abracadabra', 9, 12, WordDirection.RIGHT)]), 7+11),
    (BoardWord('abracadabra', 11, 15, WordDirection.RIGHT),
     BoardWords(words=[BoardWord('fall', 11, 14, WordDirection.DOWN),
                       BoardWord('cat', 16, 14, WordDirection.DOWN)]), 4+3),
    (BoardWord('useless', 10, 10, WordDirection.RIGHT),
     BoardWords(words=[BoardWord('scene', 16, 10, WordDirection.RIGHT),
                       BoardWord('eye', 20, 10, WordDirection.RIGHT)]), 5+3),
])
def test_board_insert_words(init_word, words, score):
    board = Board(settings=BoardSettings(width=100, height=100, init_word=init_word))

    assert board.insert_words(words) == score


@pytest.mark.parametrize("init_word,words", [
    (BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
     BoardWords(words=[BoardWord('abacaba', 10, 10, WordDirection.DOWN),
                       BoardWord('abracadabra', 10, 10, WordDirection.RIGHT)])),
    (BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
     BoardWords(words=[BoardWord('aba', 10, 10, WordDirection.RIGHT)])),
    (BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
     BoardWords(words=[BoardWord('aba', 10, 10, WordDirection.RIGHT),
                       BoardWord('abracadabra', 10, 10, WordDirection.DOWN)])),
])
def test_board_insert_words_invalid(init_word, words):
    board = Board(settings=BoardSettings(width=100, height=100, init_word=init_word))

    with pytest.raises(WordIntersectionError):
        board.insert_words(words)


def test_board_insert_words_invalid_without_init_word():
    board = Board(settings=BoardSettings(width=100, height=100))

    with pytest.raises(ValueError):
        board.insert_word(BoardWord('wordwordword', 90, 90, WordDirection.RIGHT))
    with pytest.raises(ValueError):
        board.insert_word(BoardWord('wordwordword', 90, 90, WordDirection.DOWN))


def test_board_insert_words_bonuses():
    board = Board(settings=BoardSettings(width=100, height=100, bonuses=[
        Bonus(location_x=10, location_y=10, multiplier=2), Bonus(location_x=12, location_y=10, multiplier=3)
    ]))

    assert board.insert_word(BoardWord('abacaba', 10, 10, WordDirection.DOWN)) == 7 * 2
    assert board.insert_word(BoardWord('abracadabra', 10, 10, WordDirection.RIGHT)) == 11 * (2 + 3)


@pytest.mark.parametrize("w1,w2,intersects", [
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 0, 0, WordDirection.RIGHT), True),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 4, 0, WordDirection.RIGHT), False),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 5, 0, WordDirection.RIGHT), False),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 1, 1, WordDirection.RIGHT), False),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 2, 10, WordDirection.RIGHT), False),

    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 0, 0, WordDirection.DOWN), True),
    (BoardWord('word', 3, 3, WordDirection.RIGHT), BoardWord('word', 3, 4, WordDirection.DOWN), False),
    (BoardWord('word', 1, 1, WordDirection.RIGHT), BoardWord('word', 5, 0, WordDirection.DOWN), False),
    (BoardWord('word', 1, 1, WordDirection.RIGHT), BoardWord('word', 0, 1, WordDirection.DOWN), False),

    (BoardWord('abracadabra', 11, 15, WordDirection.RIGHT), BoardWord('fall', 11, 14, WordDirection.DOWN), True),
    (BoardWord('abracadabra', 11, 15, WordDirection.RIGHT), BoardWord('cat', 16, 14, WordDirection.DOWN), True),
])
def test_board_words(w1: BoardWord, w2: BoardWord, intersects: bool):
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
    (BoardWord('word', 0, 0, WordDirection.RIGHT),
     BoardWord('word', 0, 0, WordDirection.DOWN), {(0, 0)}),
    (BoardWord('word', 0, 0, WordDirection.RIGHT),
     BoardWord('word', 0, 0, WordDirection.RIGHT), {(i, 0) for i in range(4)}),
    (BoardWord('word', 5, 5, WordDirection.RIGHT),
     BoardWord('word', 7, 3, WordDirection.DOWN), {(7, 5)}),
])
def test_board_word_intersection(w1, w2, point):
    assert w1.intersection(w2) == point
    assert w2.intersection(w1) == point
    assert w1.intersects(w2) == (point is not None)
    assert w2.intersects(w1) == (point is not None)


@pytest.mark.parametrize("w1,w2", [
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 3, 0, WordDirection.DOWN)),
    (BoardWord('word', 5, 5, WordDirection.RIGHT), BoardWord('word', 5, 3, WordDirection.DOWN)),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 2, 0, WordDirection.RIGHT)),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 1, 0, WordDirection.DOWN)),
    (BoardWord('word', 3, 3, WordDirection.RIGHT), BoardWord('word', 3, 1, WordDirection.DOWN)),
])
def test_board_word_intersection_invalid(w1, w2):
    with pytest.raises(WordIntersectionError):
        assert w1.intersection(w2)
    with pytest.raises(WordIntersectionError):
        assert w2.intersection(w1)
    with pytest.raises(WordIntersectionError):
        assert w1.intersects(w2)
    with pytest.raises(WordIntersectionError):
        assert w2.intersects(w1)


@pytest.mark.parametrize("w1,w2,intersection", [
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('word', 0, 0, WordDirection.DOWN), {(0, 0)}),
    (BoardWord('word', 0, 0, WordDirection.RIGHT), BoardWord('wiki', 0, 0, WordDirection.DOWN), {(0, 0)}),
    (BoardWord('hello', 10, 10, WordDirection.RIGHT), BoardWord('welcome', 12, 8, WordDirection.DOWN), {(12, 10)}),
    (BoardWord('hello', 10, 10, WordDirection.RIGHT), BoardWord('welcome', 11, 9, WordDirection.DOWN), {(11, 10)}),
    (BoardWord('hello', 10, 10, WordDirection.RIGHT), BoardWord('welcome', 10, 20, WordDirection.DOWN), set()),
    (BoardWord('abacaba', 10, 10, WordDirection.RIGHT), BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
     set((i, 10) for i in range(10, 17))),
])
def test_intersection(w1, w2, intersection):
    assert w1.intersection(w2) == intersection


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


@pytest.mark.parametrize("init_words,words,played_letters", [
    (None, [BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
            BoardWord('abracadabra', 10, 10, WordDirection.DOWN)],
     list('abacaba' + 'bracadabra')),
    (None, [BoardWord('abacaba', 95, 10, WordDirection.RIGHT),
            BoardWord('abracadabra', 10, 10, WordDirection.DOWN)],
     list('abacaba' + 'abracadabra')),
    (None, [BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
            BoardWord('abracadabra', 10, 12, WordDirection.DOWN)],
     list('abacaba' + 'abracadabra')),
    ([BoardWord('abacaba', 10, 10, WordDirection.RIGHT)], [BoardWord('abacaba', 10, 10, WordDirection.RIGHT),
                                                           BoardWord('abracadabra', 10, 10, WordDirection.DOWN)],
     list('bracadabra')),
    ([BoardWord('abracadabra', 10, 10, WordDirection.RIGHT)], [
        BoardWord('kaka', 10, 9, WordDirection.DOWN),
        BoardWord('fifa', 7, 12, WordDirection.RIGHT),
        BoardWord('stairs', 17, 8, WordDirection.DOWN),
        BoardWord('rain', 19, 10, WordDirection.DOWN),
        BoardWord('son', 17, 13, WordDirection.RIGHT),
    ], list('kka' + 'fif' + 'stirs' + 'ain' + 'o')),
    ([BoardWord('abracadabra', 10, 10, WordDirection.RIGHT), BoardWord('cent', 14, 10, WordDirection.DOWN)], [
        BoardWord('rust', 12, 10, WordDirection.DOWN),
        BoardWord('state', 11, 13, WordDirection.RIGHT),
    ], list('ust' + 'sae')),
])
def test_played_letters(init_words, words, played_letters):
    board = Board(settings=BoardSettings(width=100, height=100))
    if init_words:
        board.insert_words(BoardWords(words=init_words))
    assert sorted(board.get_letters_to_insert_words(BoardWords(words=words))) == sorted(played_letters)
