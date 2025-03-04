from enum import Enum
from typing import List, Optional

import tensorflow as tf
from pydantic import BaseModel


class Suit(Enum):
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    SPADES = "S"


class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Card(BaseModel):
    suit: str
    rank: int


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
