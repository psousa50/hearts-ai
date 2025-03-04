from typing import List, Optional

import tensorflow as tf
from pydantic import BaseModel, Field


class Card(BaseModel):
    suit: str = Field(..., min_length=1, max_length=1)  # Single character suit
    rank: int = Field(..., ge=2, le=14)  # Rank between 2-14


class CardMove(BaseModel):
    card: Card
    player_index: int


class Trick(BaseModel):
    cards: List[CardMove]
    winner: int


class GameState(BaseModel):
    game_id: int
    trick_number: int
    previous_tricks: List[Trick]
    current_trick_cards: List[CardMove]
    current_player_index: int
    player_hand: List[Card]
    played_card: Optional[Card] = None


def load_model(model_path):
    model = tf.keras.models.load_model(model_path)
    return model
