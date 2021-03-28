from typing import Any, List, Optional

__all__ = [
    'TextBox',
]


class TextBox:

    def __init__(self, *,
                 x: int,
                 y: int,
                 min_width: int,
                 min_height: int,
                 max_width: Optional[int] = None,
                 max_height: Optional[int] = None,
                 attrs: Optional[Any] = None):
        self._x = x
        self._y = y
        self._min_width = min_width
        self._min_height = min_height
        self._max_width = max_width
        self._max_height = max_height
        self._attrs = attrs
        self._lines: List[str] = []

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def add_line(self, line: str) -> None:
        self._lines.append(line)

    def clear(self) -> None:
        self._lines = []

    def draw(self, window) -> None:
        window_height, window_width = window.getmaxyx()

        max_height = self._max_height or window_height
        max_width = self._max_width or window_width
        box_width = max(min(window_width - self._x, max_width), self._min_width)
        box_height = max(min(window_height - self._y, max_height), self._min_height)

        trimmed_lines = []
        for line in self._lines:
            trimmed_lines.extend([line[st:st + box_width] for st in range(0, len(line), box_width)])

        x, y = self._x, self._y
        for line in trimmed_lines[-box_height:]:
            if self._attrs is not None:
                window.addstr(y, x, line, self._attrs)
            else:
                window.addstr(y, x, line)

            y += 1
