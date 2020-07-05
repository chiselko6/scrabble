from itertools import chain
from random import shuffle
from typing import Mapping

__all__ = [
    'LetterBag',
]


class LetterBag:

    def __init__(self, letters_count: int, distribution: Mapping[str, int]) -> None:
        assert all(len(letter) == 1 for letter in distribution)
        assert all(weight > 0 for weight in distribution.values())
        assert len(distribution) <= letters_count

        self._distribution = distribution
        self._letters_count = letters_count

        self._init_letters()

    def _init_letters(self) -> None:
        # each letter should occur at least once
        self._letters = [letter for letter in self._distribution]
        letters_count = self._letters_count - len(self._letters)

        total_weight = sum(self._distribution.values())
        self._letters.extend(chain.from_iterable(
            letter * round(letters_count * weight / total_weight)
            for letter, weight in self._distribution.items()
        ))

        missing_letters_count = self._letters_count - len(self._letters)
        ordered_distribution = sorted(self._distribution.items(), key=lambda it: it[1], reverse=True)
        self._letters.extend(letter for letter, _ in ordered_distribution[:missing_letters_count])
        shuffle(self._letters)

    def __iter__(self):
        return iter(self._letters)

    def __len__(self) -> int:
        return len(self._letters)

    def remove(self, key: str) -> None:
        self._letters.remove(key)
