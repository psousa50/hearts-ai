from typing import List, Optional

from hearts_game_core.game_models import Card, CompletedTrick, Trick
from pydantic import BaseModel


class GameState(BaseModel):
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    played_card: Optional[Card] = None

    def json(self, **kwargs):
        return super().model_dump_json(**kwargs)


class PredictRequest(BaseModel):
    state: GameState
    valid_moves: List[Card]

    def json(self, **kwargs):
        return super().model_dump_json(**kwargs)
