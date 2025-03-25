from dataclasses import dataclass, field
from typing import List, Optional

from hearts_game_core.game_models import Card, GameCurrentState


@dataclass
class StrategyGameState:
    game_state: GameCurrentState
    player_hand: List[Card]
    valid_moves: List[Card]



class Strategy:
    def choose_card(self, game_state: StrategyGameState) -> Card:
        raise NotImplementedError

@dataclass
class Player:
    name: str
    strategy: Strategy
    initial_hand: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    score: int = 0

