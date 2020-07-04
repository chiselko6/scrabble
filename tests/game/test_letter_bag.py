from itertools import groupby

import pytest

from scrabble.game import LetterBag


@pytest.mark.parametrize("letters_count,distribution,letters", [
    (6, {'a': 2, 'b': 4}, list('aabbbb')),
    (24, {'a': 2, 'b': 4}, list('aabbbb' * 4)),
    (10, {'a': 2}, list('a' * 10)),
    (10, {'a': 20}, list('a' * 10)),
    (10, {'a': 1}, list('a' * 10)),
    (18, {'a': 1, 'b': 2, 'c': 3}, list('abbccc' * 3)),
    (18, {'a': 1, 'b': 1, 'c': 1}, list('abc' * 6)),
    (5, {'a': 2, 'b': 4, 'c': 4}, list('abbcc')),
])
def test_letter_bag_precise_distribution(letters_count, distribution, letters):
    bag = LetterBag(letters_count, distribution)
    assert sorted(list(bag)) == sorted(letters)


@pytest.mark.parametrize("letters_count,distribution,letters", [
    (10, {'a': 1, 'b': 1, 'c': 1}, list('abc' * 3)),
    (10, {'a': 1, 'b': 2, 'c': 3}, list('abbcccbc')),
    (2, {'a': 2, 'b': 3}, list('ab')),
    (3, {'a': 2, 'b': 20}, list('abb')),
    (2, {'a': 2, 'b': 20}, list('ab')),
    (3, {'a': 2, 'b': 20, 'c': 10000}, list('abc')),
    (5, {'a': 1, 'b': 2, 'c': 3, 'd': 4}, list('abcdd')),
    (6, {'a': 1, 'b': 2, 'c': 3, 'd': 4}, list('abcdd')),
])
def test_letter_bag_approximate_distribution(letters_count, distribution, letters):
    bag = LetterBag(letters_count, distribution)
    bag_letters = list(bag)

    for letter, group in groupby(sorted(letters)):
        assert len(list(group)) <= bag_letters.count(letter)
    assert len(bag_letters) == letters_count


@pytest.mark.parametrize("letters_count,distribution", [
    (10, {'a': 3, 'b': 0}),
    (10, {'a': 1, 'b': 0}),
    (10, {'a': 0}),
    (10, {'aa': 2, 'b': 3}),
    (1, {'a': 2, 'b': 3}),
    (2, {'a': 2, 'b': 3, 'c': 4}),
])
def test_wrong_init_params(letters_count, distribution):
    with pytest.raises(AssertionError):
        LetterBag(letters_count, distribution)


@pytest.mark.parametrize("letters_count,distribution", [
    (10, {'a': 1, 'b': 2}),
    (100, {'a': 1, 'b': 1, 'c': 1}),
    (3, {'a': 1, 'b': 2, 'c': 2}),
])
def test_delete_letters(letters_count, distribution):
    bag = LetterBag(letters_count, distribution)
    bag_letters = list(bag)

    for letter in list(bag_letters):
        bag.remove(letter)
        bag_letters.remove(letter)
        assert sorted(list(bag)) == sorted(bag_letters)
