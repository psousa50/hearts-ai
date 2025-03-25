from dataclasses import dataclass, field
from typing import List, Optional

from hearts_game_core.game_models import Card, CompletedTrick, Trick


@dataclass
class StrategyGameState:
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    valid_moves: List[Card]



class Strategy:
    def choose_card(
        self, _valid_moves: List[Card], _game_state: Optional[StrategyGameState]
    ) -> Card:
        raise NotImplementedError

    @property
    def requires_game_state(self) -> bool:
        return False

@dataclass
class Player:
    name: str
    strategy: Strategy
    initial_hand: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    score: int = 0

