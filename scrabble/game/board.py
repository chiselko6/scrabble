from dataclasses import dataclass, field
from enum import Enum, unique
from typing import List, Optional, Set, Tuple

from . import constants
from .exceptions import WordIntersectionError

__all__ = [
    'WordDirection',
    'Bonus',
    'BoardSettings',
    'BoardWord',
    'BoardWords',
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

    @property
    def score(self):
        return len(self.word)

    def intersects(self, word: 'BoardWord') -> bool:
        return bool(self.intersection(word))

    def intersection(self, word: 'BoardWord') -> Set[Tuple[int, int]]:
        self.validate_intersection(word)
        return self._intersection(word)

    def _intersection(self, word: 'BoardWord') -> Set[Tuple[int, int]]:
        return set.intersection(set(self.path), set(word.path))

    def validate_intersection(self, word: 'BoardWord') -> None:
        for intersection in self._intersection(word):
            if self.letter_at(intersection[0], intersection[1]) != word.letter_at(intersection[0], intersection[1]):
                raise WordIntersectionError('Words intersection does not match')


@dataclass
class BoardWords:
    words: List[BoardWord] = field(default_factory=list)

    def __post_init__(self) -> None:
        for w1 in self.words:
            for w2 in self.words:
                w1.validate_intersection(w2)

    def __len__(self) -> int:
        return len(self.words)

    def __iter__(self):
        return iter(self.words)

    def add_word(self, word: BoardWord) -> None:
        for w in self.words:
            w.validate_intersection(word)

        self.words.append(word)

    def letter_at(self, x: int, y: int) -> Optional[str]:
        for word in self.words:
            letter = word.letter_at(x, y)
            if letter is not None:
                return letter
        return None

    def intersects(self, word: BoardWord) -> bool:
        return bool(self.intersection(word))

    def intersection(self, word: BoardWord) -> Set[Tuple[int, int]]:
        for w in self.words:
            w.validate_intersection(word)

        intersections = set()
        for w in self.words:
            intersections.update(w.intersection(word))

        return intersections


@dataclass
class BoardSettings:
    width: int
    height: int
    init_word: Optional[BoardWord] = field(default=None)
    bonuses: List[Bonus] = field(default_factory=list)

    def __post_init__(self):
        if self.width < constants.MIN_BOARD_WIDTH:
            raise ValueError(f'Board width must be at least {constants.MIN_BOARD_WIDTH}')
        if self.height < constants.MIN_BOARD_HEIGHT:
            raise ValueError(f'Board height must be at least {constants.MIN_BOARD_HEIGHT}')

        for bonus in self.bonuses:
            if not (0 <= bonus.location_x < self.width):
                raise ValueError(f'Bonus Ox position must be in 0..{self.width - 1}')
            if not (0 <= bonus.location_y < self.height):
                raise ValueError(f'Bonus Oy position must be in 0..{self.height - 1}')

        if self.init_word is not None:
            for letter_position in self.init_word.path:
                if not (0 <= letter_position[0] < self.width) or not (0 <= letter_position[1] < self.height):
                    raise ValueError('Initial word does not fit the board')


class Board:

    def __init__(self, settings: BoardSettings):
        self._settings = settings
        self._multiplier_map = [
            [1 for j in range(self._settings.width)]
            for i in range(self._settings.height)
        ]
        for bonus in self._settings.bonuses:
            self._multiplier_map[bonus.location_x][bonus.location_y] = bonus.multiplier
        self._words = BoardWords()

        if self._settings.init_word is not None:
            self.insert_word(self._settings.init_word)

    def _validate_insertion(self, word: BoardWord) -> None:
        has_letter_outside_existing_words = False

        for offset, letter in enumerate(word.word):
            if word.direction == WordDirection.RIGHT:
                x, y = word.start_x + offset, word.start_y
            else:
                x, y = word.start_x, word.start_y + offset

            if not (0 <= x < self._settings.width):
                raise ValueError('Word Ox position is out of the board')
            if not (0 <= y < self._settings.height):
                raise ValueError('Word Oy position is out of the board')

            existing_letter = self._words.letter_at(x, y)
            if existing_letter is not None and existing_letter != letter:
                raise WordIntersectionError(f'Word is not fit: {word.word}[{offset}] != {existing_letter}')
            elif existing_letter is None:
                has_letter_outside_existing_words = True

        if not has_letter_outside_existing_words:
            raise WordIntersectionError('Word consists of existing letters purely')

    def get_letters_to_insert_words(self, words: BoardWords) -> List[str]:
        current_words_positions = set()
        for w in self._words:
            current_words_positions.update(set(w.path))

        new_words_positions = set()
        for w in words:
            new_words_positions.update(set(w.path))

        new_letters: List[str] = []
        new_letters_positions = new_words_positions.difference(current_words_positions)
        for position in new_letters_positions:
            new_letters.append(words.letter_at(position[0], position[1]))  # type: ignore

        return new_letters

    def insert_words(self, words: BoardWords) -> int:
        add_score = 0
        inserted_words = set()

        # TODO: optimize
        for _ in words:
            if len(self._words) > 0:
                for idx, word in enumerate(words):
                    if idx in inserted_words:
                        continue
                    has_intersection = any(w.intersects(word) for w in self._words)
                    if has_intersection:
                        break
                else:
                    raise WordIntersectionError('New words must intersect with existing words')
            else:
                idx, word = 0, words.words[0]

            self._validate_insertion(word)
            add_score += self.word_score(word)
            self._words.add_word(word)
            inserted_words.add(idx)

        return add_score

    def insert_word(self, word: BoardWord) -> int:
        if len(self._words) > 0:
            has_intersection = any(w.intersects(word) for w in self._words)
            if not has_intersection:
                raise WordIntersectionError('New word must intersect with at least one existing word')

        self._validate_insertion(word)
        word_score = self.word_score(word)
        self._words.add_word(word)

        return word_score

    def word_score(self, word: BoardWord) -> int:
        total_multiplier = 0

        for (x, y) in word.path:
            multiplier = self._multiplier_map[x][y]
            if multiplier > 1:
                total_multiplier += multiplier

        total_multiplier = max(total_multiplier, 1)
        return word.score * total_multiplier
