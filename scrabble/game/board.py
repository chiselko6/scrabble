from dataclasses import dataclass, field
from enum import Enum, unique
from typing import List, Optional

from . import constants

__all__ = [
    'WordDirection',
    'Bonus',
    'BoardSettings',
    'BoardWord',
    'Board',
]


@unique
class WordDirection(Enum):
    RIGHT = 'right'
    DOWN = 'down'


@dataclass
class Bonus:
    location_x: int
    location_y: int
    multiplier: int

    def __post_init__(self):
        if self.location_x < 0:
            raise ValueError('Ox position must be positive')
        if self.location_y < 0:
            raise ValueError('Oy position must be positive')


@dataclass
class BoardSettings:
    width: int
    height: int
    bonuces: List[Bonus] = field(default_factory=list)

    def __post_init__(self):
        if self.width < constants.MIN_BOARD_WIDTH:
            raise ValueError(f'Board width must be at least {constants.MIN_BOARD_WIDTH}')
        if self.height < constants.MIN_BOARD_HEIGHT:
            raise ValueError(f'Board height must be at least {constants.MIN_BOARD_HEIGHT}')

        for bonus in self.bonuces:
            if not (0 <= bonus.location_x < self.width):
                raise ValueError(f'Bonus Ox position must be in 0..{self.width - 1}')
            if not (0 <= bonus.location_y < self.height):
                raise ValueError(f'Bonus Oy position must be in 0..{self.height - 1}')


@dataclass
class BoardWord:
    word: str
    start_x: int
    start_y: int
    direction: WordDirection

    @property
    def path(self):
        if self.direction == WordDirection.RIGHT:
            return [
                (self.start_x + offset, self.start_y)
                for offset in range(len(self.word))
            ]
        else:
            return [
                (self.start_x, self.start_y + offset)
                for offset in range(len(self.word))
            ]

    def letter_at(self, x: int, y: int) -> Optional[str]:
        if self.direction == WordDirection.RIGHT:
            if y != self.start_y:
                return None
            offset = x - self.start_x
        else:
            if x != self.start_x:
                return None
            offset = y - self.start_y

        if 0 <= offset < len(self.word):
            return self.word[offset]
        return None

    @property
    def position_start(self):
        return (self.start_x, self.start_y)

    @property
    def position_end(self):
        if self.direction == WordDirection.RIGHT:
            return (self.start_x + len(self.word) - 1, self.start_y)
        else:
            return (self.start_x, self.start_y + len(self.word) - 1)

    def intersects(self, word: 'BoardWord') -> bool:
        if self.direction == word.direction:
            return False

        return bool(set(self.path).intersection(set(word.path)))

    def intersection(self, word: 'BoardWord'):
        """For word with different directions - a point (coordinates) of their intersection (if one exists)"""

        if self.direction == word.direction:
            return None

        intersection = set.intersection(set(self.path), set(word.path))
        if intersection:
            return next(iter(intersection))
        return None

    def overlaps(self, word: 'BoardWord') -> bool:
        """Has "negative" meaning - `word` cannot be placed near `self`"""

        if self.direction == WordDirection.DOWN:
            self_points = set(self.path)
            self_points.update((p[0] - 1, p[1]) for p in self.path)
            self_points.update((p[0] + 1, p[1]) for p in self.path)
            self_points.add((self.start_x, self.start_y - 1))
            self_points.add((self.start_x, self.start_y + len(self.word)))
        else:
            self_points = set(self.path)
            self_points.update((p[0], p[1] - 1) for p in self.path)
            self_points.update((p[0], p[1] + 1) for p in self.path)
            self_points.add((self.start_x - 1, self.start_y))
            self_points.add((self.start_x + len(self.word), self.start_y))

        if self.direction == word.direction:
            return word.position_start in self_points or word.position_end in self_points
        else:
            w1, w2 = self, word
            if w1.direction == WordDirection.DOWN:
                w1, w2 = w2, w1

            points_below = set((p[0], p[1] + 1) for p in w1.path)
            if w2.position_start in points_below:
                return True

            points_above = set((p[0], p[1] - 1) for p in w1.path)
            if w2.position_end in points_above:
                return True

            w2_points_left = set((p[0] - 1, p[1]) for p in w2.path)
            if w1.position_end in w2_points_left:
                return True

            w2_points_right = set((p[0] + 1, p[1]) for p in w2.path)
            if w1.position_start in w2_points_right:
                return True

            return False


class Board:

    def __init__(self, settings: BoardSettings):
        self._settings = settings
        self._multiplier_map = [
            [1 for j in range(self._settings.width)]
            for i in range(self._settings.height)
        ]
        for bonus in self._settings.bonuces:
            self._multiplier_map[bonus.location_x][bonus.location_y] = bonus.multiplier

        self._words: List[BoardWord] = []

    def _validate_insertion(self, word: BoardWord) -> None:
        for offset, letter in enumerate(word.word):
            if word.direction == WordDirection.RIGHT:
                x, y = word.start_x + offset, word.start_y
            else:
                x, y = word.start_x, word.start_y + offset

            if not (0 <= x < self._settings.width):
                raise ValueError('Word Ox position is out of the board')
            if not (0 <= y < self._settings.height):
                raise ValueError('Word Oy position is out of the board')

            for existing_word in self._words:
                existing_letter = existing_word.letter_at(x, y)
                if existing_letter is not None and existing_letter != word.word[offset]:
                    raise ValueError('Word is not fit')

        for existing_word in self._words:
            if existing_word.overlaps(word):
                raise ValueError(f'New word overlaps {existing_word}')

    def insert_word(self, word: BoardWord) -> int:
        if self._words:
            has_intersection = any(w.intersects(word) for w in self._words)
            if not has_intersection:
                raise ValueError('New word must intersect at least one existing word')

        self._validate_insertion(word)

        total_multiplier = 0
        for offset, letter in enumerate(word.word):
            if word.direction == WordDirection.RIGHT:
                x, y = word.start_x + offset, word.start_y
            else:
                x, y = word.start_x, word.start_y + offset

            multiplier = self._multiplier_map[x][y]
            if multiplier > 1:
                total_multiplier += multiplier
        self._words.append(word)

        total_multiplier = max(total_multiplier, 1)
        return len(word.word) * total_multiplier

    def draw(self):
        ...
