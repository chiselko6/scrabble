from typing import Any, Optional

__all__ = [
    'TextBox',
]


class TextBox:

    def __init__(self, *, x: int, y: int, min_width: int, min_height: int, attrs: Optional[Any] = None):
        self._x = x
        self._y = y
        self._min_width = min_width
        self._min_height = min_height
        self._width = min_width
        self._height = min_height
        self._attrs = attrs
        self._lines = []

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @width.setter
    def width(self, value: int) -> None:
        self._width = max(value, self._min_width)

    @height.setter
    def height(self, value: int) -> None:
        self._height = max(value, self._min_height)

    def add_line(self, line: str) -> None:
        self._lines.append(line)

    def draw(self, window) -> None:
        trimmed_lines = []
        for line in self._lines:
            trimmed_lines.extend([line[st:st + self._width] for st in range(0, len(line), self._width)])

        x, y = self._x, self._y
        for line in trimmed_lines[-self._height:]:
            if self._attrs is not None:
                window.addstr(y, x, line, self._attrs)
            else:
                window.addstr(y, x, line)

            y += 1
