from dataclasses import dataclass, field
from typing import List

from pydantic import BaseModel

from hearts_game_core.game_models import (
    Card,
    CompletedTrick,
)
from hearts_game_core.strategies import Strategy


@dataclass
class Player:
    name: str
    strategy: Strategy
    initial_hand: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    score: int = 0


class PlayerInfo(BaseModel):
    name: str
    strategy: str
    initial_hand: List[Card] = field(default_factory=list)
    score: int


class CompletedGame(BaseModel):
    players: List[PlayerInfo]
    winner_index: int
    completed_tricks: List[CompletedTrick]
