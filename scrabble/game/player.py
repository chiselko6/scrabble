from copy import deepcopy
from dataclasses import dataclass, field
from typing import Iterable, List

__all__ = [
    'Player',
]


@dataclass
class Player:
    username: str
    score: int = field(default_factory=int)
    letters: List[str] = field(default_factory=list)

    def fulfil_letters(self, letters: Iterable[str]) -> None:
        new_player_letters = deepcopy(self.letters)

        for letter in letters:
            if len(letter) != 1:
                raise ValueError('Letters must be 1-length')

        new_player_letters.extend(letters)
        if len(new_player_letters) != 7:
            raise ValueError('Total #letters must be 7')

        self.letters = new_player_letters

    def play_letters(self, letters: Iterable[str]) -> None:
        new_player_letters = deepcopy(self.letters)

        for letter in letters:
            if letter not in self.letters:
                raise ValueError("Couldn't play missing letters")
            new_player_letters.remove(letter)

        self.letters = new_player_letters

    def add_score(self, delta: int) -> None:
        if self.score + delta < 0:
            raise ValueError("Player's score cannot be < 0")
        self.score += delta
