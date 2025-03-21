from dataclasses import dataclass
from typing import List, Optional

from hearts_game_core.game_models import Card, CompletedTrick, Trick


@dataclass
class GameState:
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    played_card: Optional[Card] = None


@dataclass
class PredictRequest:
    state: GameState
    valid_moves: List[Card]
