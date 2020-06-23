import string
from enum import Enum, unique

__all__ = [
    'WindowColor',
    'EditorMode',
    'InsertDirection',
    'KeyCode',
]


@unique
class WindowColor(Enum):
    CONNECTED_PLAYER = 1
    DISCONNECTED_PLAYER = 2
    TEMP = 3
    EDITOR_MODE = 4
    LETTER_AVAILABLE = 5
    LETTER_UNAVAILABLE = 6
    CONFIRMATION = 7
    PLAYER_STATUS = 8
    BONUS = 9
    TUTORIAL = 10


@unique
class EditorMode(Enum):
    INSERT = 1
    VIEW = 2
    CONFIRMATION = 3
    DELETE_PLAYER_LETTERS = 4
    ADD_PLAYER_LETTERS = 5


@unique
class InsertDirection(Enum):
    RIGHT = 1
    DOWN = 2


@unique
class KeyCode(Enum):
    ENTER = 13
    ESCAPE = 27
    BACKSPACE = 8
    DELETE = 127
    APPROVE = ord('y')
    REJECT = ord('n')


GRID_WIDTH = 30
GRID_HEIGHT = 30
GRID_X = 4
GRID_Y = 4

LETTERS_OFFSET_Y = 2
LETTERS_OFFSET_X = GRID_WIDTH // 2 - 3

DEBUG_BOX_X = GRID_X + GRID_WIDTH * 2 + 40
DEBUG_BOX_Y = 3
DEBUG_BOX_WIDTH = 80
DEBUG_BOX_HEIGHT = 50

TUTORIAL_BOX_X = 3
TUTORIAL_BOX_Y = GRID_Y + GRID_HEIGHT + LETTERS_OFFSET_Y * 2
TUTORIAL_BOX_WIDTH = 95
TUTORIAL_BOX_HEIGHT = 15

PLAYERS_STATUS_X = 70
PLAYERS_STATUS_Y = 4

CONFIRMATION_DIALOG_X = 5
CONFIRMATION_DIALOG_Y = GRID_Y + GRID_HEIGHT + 15

LETTERS = set(ord(ch) for ch in string.ascii_uppercase + string.ascii_lowercase)

SLEEP_BETWEEN_INPUT = 0.01  # sec
