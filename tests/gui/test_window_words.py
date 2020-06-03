from copy import deepcopy

import pytest

from scrabble.gui import WindowBonus, WindowBonuses, WindowWord, WindowWords


@pytest.mark.parametrize("word,add_letters", [
    (WindowWord(), [(0, 0, 'a'), (0, 1, 'b'), (0, 2, 'c'), (0, 3, 'd')]),
    (WindowWord(path=[(0, 4)], letters=['e']), [(0, 0, 'a'), (0, 1, 'b'), (0, 2, 'c'), (0, 3, 'd')]),
    (WindowWord(path=[(0, 0)], letters=['a']), [(1, 0, 'b'), (2, 0, 'b'), (3, 0, 'c')]),
])
def test_window_word(word, add_letters):
    initial_word = deepcopy(word)
    initial_path = deepcopy(word.path)
    initial_letters = deepcopy(word.letters)

    new_path = []
    new_letters = []
    for (x, y, letter) in add_letters:
        word.add_letter(x, y, letter)
        new_path.append((x, y))
        new_letters.append(letter)

        assert word.path == initial_path + new_path
        assert word.letters == initial_letters + new_letters

    cpy_word = deepcopy(word)
    for (x, y) in cpy_word.path:
        letter = word.pop_letter(x, y)
        assert letter == cpy_word.letter_at(x, y)

    cpy_word2 = deepcopy(cpy_word)
    assert len(cpy_word2) == len(initial_word) + len(add_letters)

    letters = deepcopy(cpy_word2.letters)
    for i in range(len(cpy_word2)):
        letter = cpy_word2.pop_letter()
        assert letter == letters[-i - 1]
        assert len(cpy_word2) == len(letters) - i - 1


def test_window_words():
    path1 = [(0, 0), (0, 1), (0, 2), (0, 3)]
    letters1 = ['a', 'b', 'c', 'd']
    path2 = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
    letters2 = ['a', 'x', 'y', 'z', 't']
    words = WindowWords(words=[WindowWord(path=path1, letters=letters1),
                               WindowWord(path=path2, letters=letters2)])

    for position, letter in zip(path1 + path2, letters1 + letters2):
        assert letter == words.letter_at(position[0], position[1])
        assert words.letter_at(position[0] + 10, position[1] + 10) is None
        assert words.is_filled(position[0], position[1])
        assert not words.is_filled(position[0] + 10, position[1] + 10)

    words.clear()
    assert len(words.words) == 0


def test_window_bonuses():
    bonus_1 = WindowBonus(x=10, y=10, multiplier=2)
    bonus_2 = WindowBonus(x=11, y=11, multiplier=3)
    bonus_3 = WindowBonus(x=12, y=20, multiplier=8)
    bonuses = WindowBonuses(bonuses=[bonus_1, bonus_2, bonus_3])

    assert bonuses.bonus_at(bonus_1.x, bonus_1.y) == bonus_1
    assert bonuses.bonus_at(bonus_2.x, bonus_2.y) == bonus_2
    assert bonuses.bonus_at(bonus_3.x, bonus_3.y) == bonus_3
    assert bonuses.bonus_at(100, 100) is None
