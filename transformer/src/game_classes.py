from typing import List, Optional

from pydantic import BaseModel


class Card(BaseModel):
    suit: str
    rank: int

    def __str__(self):
        return f"{self.rank}{self.suit}"


class Trick(BaseModel):
    cards: List[Optional[Card]]
    first_player_index: int

    def ordered_cards(self):
        return [
            card
            for card in (
                self.cards[self.first_player_index :]
                + self.cards[: self.first_player_index]
            )
            if card is not None
        ]


class CompletedTrick(BaseModel):
    cards: List[Card]
    first_player_index: int
    winner: int
    score: int

    def ordered_cards(self):
        return [
            card
            for card in (
                self.cards[self.first_player_index :]
                + self.cards[: self.first_player_index]
            )
        ]


class GameState(BaseModel):
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    played_card: Optional[Card] = None
