import curses
import logging
from collections import Counter
from copy import deepcopy
from curses import error
from dataclasses import dataclass, field
from time import sleep
from typing import Callable, Iterable, List, MutableSet, Optional, Tuple

from .components import TextBox
from .constants import (CONFIRMATION_DIALOG_X, CONFIRMATION_DIALOG_Y, CONTROLS, GRID_HEIGHT, GRID_WIDTH, GRID_X, GRID_Y,
                        LETTERS, LETTERS_OFFSET_X, LETTERS_OFFSET_Y, PLAYERS_STATUS_X, PLAYERS_STATUS_Y,
                        SLEEP_BETWEEN_INPUT, TUTORIAL_BOX_X, TUTORIAL_BOX_Y, EditorMode, InsertDirection, KeyCode,
                        WindowColor)

__all__ = [
    'Window',
    'WindowWord',
    'WindowWords',
    'WindowBonus',
    'WindowBonuses',
]


@dataclass
class CallbackConfig:
    # Callable(words[start_x, start_y, word, direction], letters)
    on_player_move: Optional[Callable[[Iterable[Tuple[int, int, str, str]], List[str]], None]] = field(default=None)


@dataclass
class WindowWord:
    path: List[Tuple[int, int]] = field(default_factory=list)
    letters: List[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.path)

    def is_filled(self, x: int, y: int) -> bool:
        return (x, y) in self.path

    def letter_at(self, x: int, y: int) -> Optional[str]:
        for position, letter in zip(self.path, self.letters):
            if position == (x, y):
                return letter
        return None

    def add_letter(self, x: int, y: int, letter: str) -> None:
        self.path.append((x, y))
        self.letters.append(letter)

    def pop_letter(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        if x is None:
            assert y is None

            self.path.pop()
            return self.letters.pop()
        else:
            assert y is not None

            if (x, y) not in self.path:
                raise KeyError()
            else:
                idx = self.path.index((x, y))
                letter = self.letters[idx]

                del self.path[idx]
                del self.letters[idx]

                return letter


@dataclass
class WindowWords:
    words: List[WindowWord] = field(default_factory=list)

    def __iter__(self):
        return iter(self.words)

    def is_filled(self, x: int, y: int) -> bool:
        for word in self.words:
            if word.is_filled(x, y):
                return True

        return False

    def letter_at(self, x: int, y: int) -> Optional[str]:
        for word in self.words:
            letter = word.letter_at(x, y)
            if letter is not None:
                return letter
        return None

    def clear(self):
        self.words.clear()


@dataclass
class WindowBonus:
    x: int
    y: int
    multiplier: int

    @property
    def position(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass
class WindowBonuses:
    bonuses: List[WindowBonus] = field(default_factory=list)

    def __iter__(self):
        return iter(self.bonuses)

    def bonus_at(self, x: int, y: int) -> Optional[WindowBonus]:
        for bonus in self.bonuses:
            if bonus.position == (x, y):
                return bonus
        return None


class Window:

    def __init__(self, player: str, callback_config: Optional[CallbackConfig] = None) -> None:
        self._logger = logging.getLogger()

        self._editor_mode: EditorMode = EditorMode.VIEW
        self._can_change_editor_mode = False
        self._insert_mode_direction: Optional[InsertDirection] = None

        self._grid_words = WindowWords()
        self._recently_added_words = WindowWords()
        # added on player's turn
        self._temp_words = WindowWords()
        self._bonuses = WindowBonuses()

        self._running = False

        self._player = player
        self._player_turn: Optional[str] = None
        self._players: List[str] = []
        self._players_scores = {player: 0 for player in self._players}
        self._recent_player_score_change: Optional[Tuple[str, int]] = None
        self._players_connected: MutableSet[str] = set()
        self._player_letters: List[str] = []
        self._player_letters_to_remove: List[str] = []

        self._language = 'en'

        self._callbacks = callback_config or CallbackConfig()

        self._show_confirmation_dialog = False
        self._confirmation_callback: Optional[Callable[[], None]] = None

    @property
    def running(self) -> bool:
        return self._running

    def set_language(self, lang: str) -> None:
        self._language = lang

    def set_player_turn(self, player: str) -> None:
        self._player_turn = player
        self._can_change_editor_mode = self._player_turn == self._player

        self.draw()

    def _clear_recent_changes(self) -> None:
        self._recent_player_score_change = None
        self._recently_added_words.clear()

    def register_callback(self, cb: CallbackConfig) -> None:
        self._callbacks.on_player_move = cb.on_player_move

    def player_connected(self, player) -> None:
        self._logger.info(f'Connected player "{player}"')

        self._players_connected.add(player)

        self.draw()

    def player_disconnected(self, player) -> None:
        self._logger.info(f'Disconnected player "{player}"')

        if player in self._players_connected:
            self._players_connected.remove(player)

        self.draw()

    def add_player(self, player: str, connected: bool = False) -> None:
        self._players.append(player)
        self._players_scores[player] = 0
        if connected:
            self._players_connected.add(player)

        self.draw()

    def update_player_score(self, player: str, new_score: int) -> None:
        diff = new_score - self._players_scores[player]

        self._players_scores[player] = new_score
        self._recent_player_score_change = (player, diff)

        self.draw()

    def cancel_move(self) -> None:
        curses.beep()

        cleared_positions: MutableSet[Tuple[int, int]] = set()

        for word in self._temp_words:
            while len(word) > 0:
                letter_position = word.path[-1]
                letter = word.pop_letter()
                if letter_position not in cleared_positions and \
                   not self._grid_words.is_filled(letter_position[0], letter_position[1]):
                    self._player_letters.append(letter)
                    cleared_positions.add(letter_position)

        self._temp_words.clear()
        self._player_letters_to_remove.clear()

        self.draw()

    def add_grid_words(self, words: Iterable[Tuple[int, int, str, str]]) -> None:
        self._temp_words.clear()
        self._clear_recent_changes()

        for word in words:
            self._add_grid_word(*word)

        self.draw()

    def _add_grid_word(self, start_x: int, start_y: int, word: str, direction: str) -> None:
        window_word = WindowWord()

        for offset, letter in enumerate(word):
            # TODO
            if direction == 'right':
                grid_x, grid_y = start_x + offset, start_y
            else:
                grid_x, grid_y = start_x, start_y + offset

            assert 0 <= grid_x < GRID_WIDTH
            assert 0 <= grid_y < GRID_HEIGHT

            window_word.path.append((grid_x, grid_y))
            window_word.letters.append(letter)

        self._grid_words.words.append(window_word)
        self._recently_added_words.words.append(window_word)

    def add_bonus(self, x: int, y: int, multiplier: int) -> None:
        self._bonuses.bonuses.append(WindowBonus(x=x, y=y, multiplier=multiplier))
        self.draw()

    def update_player_letters(self, letters: Iterable[str]) -> None:
        assert all([len(letter) == 1 for letter in letters])

        self._player_letters = list(letters)
        self._player_letters_to_remove.clear()
        self.draw()

    def draw_player_status(self) -> None:
        self._window.addstr(GRID_Y - 2, GRID_X + GRID_WIDTH // 2,
                            self._player,
                            curses.color_pair(WindowColor.PLAYER_STATUS.value) | curses.A_BOLD)

    def draw_player_letters(self):
        letters_to_remove = deepcopy(self._player_letters_to_remove)
        for idx, letter in enumerate(self._player_letters):
            if letter in letters_to_remove:
                attrs = curses.color_pair(WindowColor.LETTER_UNAVAILABLE.value)
                letters_to_remove.remove(letter)
            else:
                attrs = curses.color_pair(WindowColor.LETTER_AVAILABLE.value)
            if self._editor_mode in (EditorMode.DELETE_PLAYER_LETTERS, EditorMode.ADD_PLAYER_LETTERS):
                attrs |= curses.A_UNDERLINE
            self._window.addch(GRID_Y + GRID_HEIGHT + LETTERS_OFFSET_Y,
                               GRID_X + LETTERS_OFFSET_X + idx * 3,
                               letter,
                               attrs)

    def draw_grid(self):
        # border
        for y in range(GRID_Y, GRID_Y + GRID_HEIGHT):
            self._window.addch(y, GRID_X - 1, '|')
            self._window.addch(y, GRID_X + GRID_WIDTH * 2 - 1, '|')
        for x in range(GRID_X, GRID_X + GRID_WIDTH * 2 - 1):
            self._window.addch(GRID_Y - 1, x, '-')
            self._window.addch(GRID_Y + GRID_HEIGHT, x, '-')

        # letters
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                grid_x, grid_y = GRID_X + x * 2, GRID_Y + y
                if self._temp_words.is_filled(x, y):
                    letter = self._temp_words.letter_at(x, y)
                    self._window.addch(grid_y, grid_x, letter,
                                       curses.color_pair(WindowColor.TEMP.value))
                elif self._recently_added_words.is_filled(x, y):
                    letter = self._recently_added_words.letter_at(x, y)
                    self._window.addch(grid_y, grid_x, letter,
                                       curses.color_pair(WindowColor.RECENT_CHANGE.value))
                else:
                    ch = self._grid_words.letter_at(x, y)
                    if ch is not None:
                        if self._editor_mode == EditorMode.INSERT:
                            self._window.addch(grid_y, grid_x, ch, curses.A_UNDERLINE)
                        else:
                            self._window.addch(grid_y, grid_x, ch)

    def draw_players_status(self):
        for idx, player in enumerate(self._players):
            if player in self._players_connected:
                color = WindowColor.CONNECTED_PLAYER.value
            else:
                color = WindowColor.DISCONNECTED_PLAYER.value
            player_attrs = curses.color_pair(color)
            if self._player_turn == player:
                player_attrs |= curses.A_UNDERLINE | curses.A_BOLD

            status_position_start = (PLAYERS_STATUS_X, PLAYERS_STATUS_Y + idx * 2)
            player_score = self._players_scores[player]
            self._window.addstr(status_position_start[1],
                                status_position_start[0], player, player_attrs)
            self._window.addstr(status_position_start[1],
                                status_position_start[0] + len(player) + 2, str(player_score))

            if self._recent_player_score_change is not None:
                recent_player_changed, score_changed = self._recent_player_score_change

                if player == recent_player_changed:
                    self._window.addstr(
                        status_position_start[1],
                        status_position_start[0] + len(player) + 2 + len(str(player_score)) + 1,
                        f'(+{score_changed})',
                        curses.color_pair(WindowColor.RECENT_CHANGE.value))

    def draw_editor_mode(self):
        height, width = self._window.getmaxyx()
        mode_str = f'Mode: {self._editor_mode.name}'
        self._window.addstr(height - 1, 0, mode_str, curses.color_pair(WindowColor.EDITOR_MODE.value))

    def draw_confirmation_dialog(self):
        if self._show_confirmation_dialog:
            if self._language == 'en':
                desc = 'Confirm? Y / N'
            else:
                desc = 'Подтверждение? Д / Н'

            self._window.addstr(CONFIRMATION_DIALOG_Y,
                                CONFIRMATION_DIALOG_X,
                                desc,
                                curses.color_pair(WindowColor.CONFIRMATION.value))

    def grid_to_window_position(self, position: Tuple[int, int]) -> Tuple[int, int]:
        x, y = position
        return (GRID_X + x * 2, GRID_Y + y)

    def draw_bonuses(self):
        for bonus in self._bonuses:
            if not self._grid_words.is_filled(bonus.x, bonus.y) and not self._temp_words.is_filled(bonus.x, bonus.y):
                x, y = self.grid_to_window_position(bonus.position)
                self._window.addch(y, x, str(bonus.multiplier), curses.color_pair(WindowColor.BONUS.value))

    def init_colors(self) -> None:
        curses.init_pair(WindowColor.CONNECTED_PLAYER.value, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(WindowColor.DISCONNECTED_PLAYER.value, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(WindowColor.TEMP.value, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(WindowColor.EDITOR_MODE.value, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(WindowColor.LETTER_AVAILABLE.value, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(WindowColor.LETTER_UNAVAILABLE.value, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(WindowColor.CONFIRMATION.value, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(WindowColor.PLAYER_STATUS.value, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(WindowColor.BONUS.value, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(WindowColor.TUTORIAL.value, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(WindowColor.RECENT_CHANGE.value, curses.COLOR_CYAN, curses.COLOR_BLACK)

    def draw_tutorial(self) -> None:
        self._tutorial_box.clear()

        ru_text = [
            '<я>: Выйти из игры/закончить сессию ввода.',
            '<у>: Начать _у_далять буквы игрока для обмена.',
            '<м>: Начать возвращать удаленные для об_м_ена буквы игрока.',
            '<с>: _С_охранить прогресс и сделать ход.',
            '<о>: _О_тменить текущий прогресс. Будут удалены все временно введенные '
            'буквы и помеченные для обмена буквы игрока.',
            '<в>: Начать _в_водить буквы в игровое поле. Можно использовать ТОЛЬКО буквы '
            'из текущего состояния. После нажатия клавиши, необходимо выбрать направление '
            'вставки слова: <вниз> или <вправо> (стрелками).',
            '<д>: Подтвердить выбор (_д_а).',
            '<н>: Отменить выбор (_н_ет).',
        ]
        en_text = [
            '<d>: Start _d_eleting player letters for exchange.',
            '<i>: Start _i_nserting words to the grid. You can use ONLY '
            'the letters from your current state. After pressing <i>, you should '
            'choose the direction to insert your words: <j> (for down) or <l> (for right).',
            '<a>: Start _a_ppending back removed letters for exchange.',
            '<s>: _S_ave your progress and move.',
            '<c>: _C_ancel your progress. This will delete all your temporary inserted grid '
            'words and removed letters.',
            '<y>: Confirm your move.',
            '<n>: Unconfirm your move.',
        ]

        if self._language == 'ru':
            text = ru_text
        else:
            text = en_text

        for line in text:
            self._tutorial_box.add_line(line)

        self._tutorial_box.draw(self._window)

    def draw(self) -> None:
        self._window.clear()

        self.draw_grid()
        self.draw_player_status()
        self.draw_players_status()
        self.draw_editor_mode()
        self.draw_player_letters()
        self.draw_confirmation_dialog()
        self.draw_tutorial()
        self.draw_bonuses()

        self._window.move(self._cursor_y, self._cursor_x)

    def _clear_player_values(self) -> None:
        cleared_positions: MutableSet[Tuple[int, int]] = set()

        for word in self._temp_words:
            for ch, position in zip(word.letters, word.path):
                if position not in cleared_positions and not self._grid_words.is_filled(position[0], position[1]):
                    self._player_letters.append(ch)
                    cleared_positions.add(position)

        self._temp_words.clear()
        self._player_letters_to_remove.clear()

    def _getch(self) -> int:
        while True:
            sleep(SLEEP_BETWEEN_INPUT)

            try:
                ch = self._window.get_wch()
            except error:
                continue

            if isinstance(ch, str):
                return ord(ch)
            return ch

    def _play(self) -> None:
        player_move_words = []
        for word in self._temp_words:
            if len(word) > 1:
                if word.path[0][0] != word.path[1][0]:
                    direction = 'right'
                else:
                    direction = 'down'
            elif len(word) == 1:
                direction = 'right'
            else:
                continue
            player_move_words.append((word.path[0][0],
                                      word.path[0][1],
                                      ''.join(word.letters), direction))

        cb = self._callbacks.on_player_move

        if cb is not None:
            cb(player_move_words, self._player_letters_to_remove)

    def run(self, window) -> None:
        self._running = True
        self._window = window
        self._window.nodelay(True)
        self._height, self._width = self._window.getmaxyx()
        self._cursor_y, self._cursor_x = GRID_Y, GRID_X

        self._tutorial_box = TextBox(
            x=TUTORIAL_BOX_X,
            y=TUTORIAL_BOX_Y,
            min_width=10,
            min_height=10,
            attrs=curses.color_pair(WindowColor.TUTORIAL.value),
        )

        self._window.clear()
        self._window.refresh()

        curses.start_color()
        self.init_colors()

        # start
        self.draw()

        while True:
            ch = self._getch()
            self._logger.debug(f'<{self._editor_mode.name}>: "{chr(ch)}"({ch})')

            if self._editor_mode == EditorMode.VIEW:
                if chr(ch) in CONTROLS[self._language].close:
                    break

                elif chr(ch) in CONTROLS[self._language].delete:
                    if not self._can_change_editor_mode:
                        curses.beep()
                        continue

                    self._clear_recent_changes()

                    self._editor_mode = EditorMode.DELETE_PLAYER_LETTERS

                elif chr(ch) in CONTROLS[self._language].add_player_letters:
                    if not self._can_change_editor_mode:
                        curses.beep()
                        continue

                    self._clear_recent_changes()

                    self._editor_mode = EditorMode.ADD_PLAYER_LETTERS

                elif chr(ch) in CONTROLS[self._language].save:
                    if not self._can_change_editor_mode:
                        curses.beep()
                        continue

                    self._clear_recent_changes()

                    self._confirmation_callback = self._play
                    self._editor_mode = EditorMode.CONFIRMATION
                    self._show_confirmation_dialog = True

                elif chr(ch) in CONTROLS[self._language].cancel:
                    if not self._can_change_editor_mode:
                        curses.beep()
                        continue

                    self._clear_recent_changes()

                    self._confirmation_callback = self._clear_player_values
                    self._editor_mode = EditorMode.CONFIRMATION
                    self._show_confirmation_dialog = True

                elif chr(ch) in CONTROLS[self._language].move_down:
                    self._cursor_y += 1
                elif chr(ch) in CONTROLS[self._language].move_up:
                    self._cursor_y -= 1
                elif chr(ch) in CONTROLS[self._language].move_right:
                    self._cursor_x += 2
                elif chr(ch) in CONTROLS[self._language].move_left:
                    self._cursor_x -= 2

                elif chr(ch) in CONTROLS[self._language].insert:
                    if not self._can_change_editor_mode:
                        curses.beep()
                        continue

                    self._logger.debug(f'<{self._editor_mode.name}>: Starting <INSERT>')
                    ch = self._getch()
                    self._logger.debug(f'<{self._editor_mode.name}>: Choosing direction: "{chr(ch)}"({ch})')
                    if ch == KeyCode.ESCAPE.value:
                        continue

                    if chr(ch) in CONTROLS[self._language].move_right:
                        self._insert_direction = InsertDirection.RIGHT
                    elif chr(ch) in CONTROLS[self._language].move_down:
                        self._insert_direction = InsertDirection.DOWN
                    else:
                        curses.beep()
                        continue

                    self._clear_recent_changes()

                    self.toggle_editor_mode()
                    self._temp_words.words.append(WindowWord())

            elif self._editor_mode == EditorMode.CONFIRMATION:
                if chr(ch) in CONTROLS[self._language].confirm.union(CONTROLS[self._language].reject):
                    if chr(ch) in CONTROLS[self._language].confirm:
                        assert self._confirmation_callback is not None
                        self._confirmation_callback()
                        self._confirmation_callback = None

                    self._show_confirmation_dialog = False
                    self._editor_mode = EditorMode.VIEW
                else:
                    curses.beep()
            elif self._editor_mode == EditorMode.INSERT:
                if ch in (KeyCode.ENTER.value, curses.KEY_ENTER, KeyCode.ESCAPE.value):
                    self.toggle_editor_mode()
                    continue

                elif ch in LETTERS[self._language]:
                    grid_x, grid_y = (self._cursor_x - GRID_X) // 2, self._cursor_y - GRID_Y

                    grid_letter = self._grid_words.letter_at(grid_x, grid_y)
                    if grid_letter is not None:
                        if grid_letter != chr(ch):
                            curses.beep()
                        else:
                            if ((self._insert_direction == InsertDirection.RIGHT and grid_x == GRID_WIDTH - 1) or
                                (self._insert_direction == InsertDirection.DOWN and grid_y == GRID_HEIGHT - 1)) and \
                               self._temp_words.words[-1].is_filled(grid_x, grid_y):
                                curses.beep()
                            else:
                                self._temp_words.words[-1].add_letter(grid_x, grid_y, chr(ch))
                                if self._insert_direction == InsertDirection.RIGHT:
                                    self._cursor_x += 2
                                else:
                                    self._cursor_y += 1
                    else:
                        existing_temp_letter = self._temp_words.letter_at(grid_x, grid_y)
                        self._logger.debug(f'Existing temp letter: "{existing_temp_letter or "_"}"')
                        if existing_temp_letter is not None:
                            self._logger.debug(chr(ch))
                            self._logger.debug(existing_temp_letter == chr(ch))
                            if existing_temp_letter != chr(ch):
                                curses.beep()
                                continue
                        else:
                            available_letters = Counter(self._player_letters)
                            available_letters.subtract(Counter(self._player_letters_to_remove))
                            if not available_letters.get(chr(ch)):
                                curses.beep()
                                continue

                        assert isinstance(self._insert_direction, InsertDirection)
                        if ((self._insert_direction == InsertDirection.RIGHT and grid_x == GRID_WIDTH - 1) or
                            (self._insert_direction == InsertDirection.DOWN and grid_y == GRID_HEIGHT - 1)) and \
                           self._temp_words.words[-1].is_filled(grid_x, grid_y):
                            curses.beep()
                            continue

                        self._temp_words.words[-1].add_letter(grid_x, grid_y, chr(ch))
                        if existing_temp_letter is None:
                            self._player_letters.remove(chr(ch))

                        if self._insert_direction == InsertDirection.RIGHT:
                            self._cursor_x += 2
                        else:
                            self._cursor_y += 1

                elif ch in (KeyCode.BACKSPACE.value, KeyCode.DELETE.value):
                    assert isinstance(self._insert_direction, InsertDirection)

                    grid_x, grid_y = (self._cursor_x - GRID_X) // 2, self._cursor_y - GRID_Y
                    if ((self._insert_direction == InsertDirection.RIGHT and grid_x == GRID_WIDTH - 1) or
                        (self._insert_direction == InsertDirection.DOWN and grid_y == GRID_HEIGHT - 1)) and \
                       self._temp_words.words[-1].is_filled(grid_x, grid_y):
                        letter = self._temp_words.words[-1].pop_letter(grid_x, grid_y)

                        if not self._grid_words.is_filled(grid_x, grid_y) and \
                           not self._temp_words.is_filled(grid_x, grid_y):
                            self._player_letters.append(letter)
                    else:
                        if self._insert_direction == InsertDirection.RIGHT:
                            if self._temp_words.words[-1].is_filled(grid_x - 1, grid_y):
                                self._cursor_x -= 2
                                letter = self._temp_words.words[-1].pop_letter(grid_x - 1, grid_y)
                                if not self._grid_words.is_filled(grid_x - 1, grid_y) and \
                                   not self._temp_words.is_filled(grid_x - 1, grid_y):
                                    self._player_letters.append(letter)
                            else:
                                curses.beep()
                        else:
                            if self._temp_words.words[-1].is_filled(grid_x, grid_y - 1):
                                self._cursor_y -= 1
                                letter = self._temp_words.words[-1].pop_letter(grid_x, grid_y - 1)
                                if not self._grid_words.is_filled(grid_x, grid_y - 1) and \
                                   not self._temp_words.is_filled(grid_x, grid_y - 1):
                                    self._player_letters.append(letter)
                            else:
                                curses.beep()

            elif self._editor_mode == EditorMode.DELETE_PLAYER_LETTERS:
                if ch in (KeyCode.ESCAPE.value, KeyCode.ENTER.value):
                    self._editor_mode = EditorMode.VIEW
                else:
                    letter = chr(ch)
                    if self._player_letters.count(letter) > self._player_letters_to_remove.count(letter):
                        self._player_letters_to_remove.append(letter)
                    else:
                        curses.beep()

            elif self._editor_mode == EditorMode.ADD_PLAYER_LETTERS:
                if ch in (KeyCode.ESCAPE.value, KeyCode.ENTER.value):
                    self._editor_mode = EditorMode.VIEW
                else:
                    letter = chr(ch)
                    if letter in self._player_letters_to_remove:
                        self._player_letters_to_remove.remove(letter)
                    else:
                        curses.beep()
            else:
                curses.beep()

            self._safe_move_cursor()
            self.draw()

        self._running = False

    def toggle_editor_mode(self):
        if self._editor_mode == EditorMode.INSERT:
            self._editor_mode = EditorMode.VIEW
            self._insert_direction = None
        elif self._editor_mode == EditorMode.VIEW:
            self._editor_mode = EditorMode.INSERT
        else:
            raise ValueError(f'Unknown editor mode {self._editor_mode}')

    def _safe_move_cursor(self) -> None:
        self._cursor_x = max(GRID_X, self._cursor_x)
        self._cursor_x = min(GRID_X + GRID_WIDTH * 2 - 2, self._cursor_x)
        self._cursor_y = max(GRID_Y, self._cursor_y)
        self._cursor_y = min(GRID_Y + GRID_HEIGHT - 1, self._cursor_y)

        self._window.move(self._cursor_y, self._cursor_x)
