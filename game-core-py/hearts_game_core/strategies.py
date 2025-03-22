from dataclasses import dataclass
from typing import List

from hearts_game_core.game_models import Card, CompletedTrick, Trick


@dataclass
class StrategyGameState:
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    valid_moves: List[Card]


class Strategy:
    def choose_card(self, gameState: StrategyGameState) -> Card:
        raise NotImplementedError
