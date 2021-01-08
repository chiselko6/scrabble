import curses
import string
from collections import namedtuple
from enum import Enum, unique

__all__ = [
    'WindowColor',
    'EditorMode',
    'InsertDirection',
    'KeyCode',
    'ActionChars',
    'CONTROLS',
]


LOG_FILE = '/tmp/scrabble/logs.txt'


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
    RECENT_CHANGE = 11


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


GRID_WIDTH = 20
GRID_HEIGHT = 20
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

PLAYERS_STATUS_X = GRID_X + 2 * GRID_WIDTH + 10
PLAYERS_STATUS_Y = 4

CONFIRMATION_DIALOG_X = 5
CONFIRMATION_DIALOG_Y = GRID_Y + GRID_HEIGHT + 15

LETTERS = {
    'en': set(ord(ch) for ch in string.ascii_uppercase + string.ascii_lowercase),
    'ru': set(map(ord, 'АаБбВвГгДдЕеЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя')),
}

SLEEP_BETWEEN_INPUT = 0.01  # sec


ActionChars = namedtuple('ActionChars', ['close', 'delete', 'add_player_letters', 'save',
                                         'cancel', 'move_up', 'move_down', 'move_left',
                                         'move_right', 'insert', 'confirm', 'reject'])

CONTROLS = {
    'en': ActionChars(
        close={'q'},
        delete={'d'},
        add_player_letters={'a'},
        save={'s'},
        cancel={'c'},
        move_up={chr(curses.KEY_UP), 'k'},
        move_down={chr(curses.KEY_DOWN), 'j'},
        move_left={chr(curses.KEY_LEFT), 'h'},
        move_right={chr(curses.KEY_RIGHT), 'l'},
        insert={'i', chr(curses.KEY_ENTER), chr(KeyCode.ENTER.value)},
        confirm={'y'},
        reject={'n'},
    ),
    'ru': ActionChars(
        close={'я'},
        delete={'у'},
        add_player_letters={'м'},
        save={'с'},
        cancel={'о'},
        move_up={chr(curses.KEY_UP)},
        move_down={chr(curses.KEY_DOWN)},
        move_left={chr(curses.KEY_LEFT)},
        move_right={chr(curses.KEY_RIGHT)},
        insert={'в', chr(curses.KEY_ENTER), chr(KeyCode.ENTER.value)},
        confirm={'д'},
        reject={'н'},
    ),
}
