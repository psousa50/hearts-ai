from typing import List, Optional

from pydantic import BaseModel


class Card(BaseModel):
    suit: str
    rank: int


class Trick(BaseModel):
    cards: List[Optional[Card]]
    first_player_index: int


class CompletedTrick(BaseModel):
    cards: List[Card]
    first_player_index: int
    winner: int
    score: int


class GameState(BaseModel):
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    played_card: Optional[Card] = None


class PredictRequest(BaseModel):
    state: GameState
    valid_moves: List[Card]
