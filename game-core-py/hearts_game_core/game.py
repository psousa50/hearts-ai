from dataclasses import dataclass
from typing import List

from pydantic import BaseModel

from hearts_game_core.game_models import (
    CompletedTrick,
)
from hearts_game_core.strategies import Strategy


@dataclass
class Player:
    name: str
    strategy: Strategy


class PlayerInfo(BaseModel):
    name: str
    strategy: str
    score: int


class CompletedGame(BaseModel):
    players: List[PlayerInfo]
    winner_index: int
    completed_tricks: List[CompletedTrick]
