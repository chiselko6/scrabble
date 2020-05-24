from dataclasses import dataclass, field
from typing import List, Optional

from scrabble.game.board import BoardSettings

from .base import Event


@dataclass
class GameInitParams:
    players: List[str]
    board_settings: BoardSettings


class GameInitEvent(Event):
    params: GameInitParams


@dataclass
class GameStartParams:
    player_to_start: Optional[str] = field(default=None)


class GameStartEvent(Event):
    params: GameStartParams
