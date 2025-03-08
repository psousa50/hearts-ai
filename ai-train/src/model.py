from typing import List, Optional

import tensorflow as tf
from pydantic import BaseModel, Field


class Card(BaseModel):
    suit: str = Field(..., min_length=1, max_length=1)  # Single character suit
    rank: int = Field(..., ge=2, le=14)  # Rank between 2-14


class Trick(BaseModel):
    cards: List[Optional[Card]]
    first_player: int


class CompletedTrick(BaseModel):
    cards: List[Card]
    first_player: int
    winner: int
    score: int


class GameState(BaseModel):
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    played_card: Optional[Card] = None


def load_model(model_path):
    model = tf.keras.models.load_model(model_path)
    return model
