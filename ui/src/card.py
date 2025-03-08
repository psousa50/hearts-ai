from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Card:
    suit: str
    rank: int

    def __str__(self):
        return f"{self.rank}{self.suit}"

    QueenOfSpades = None


Card.QueenOfSpades = Card("S", 12)


@dataclass
class Trick:
    cards: List[Optional[Card]] = field(init=False)
    first_player_index: int = field(init=False)

    def __post_init__(self):
        self.reset()

    @property
    def size(self):
        return len([card for card in self.cards if card is not None])

    @property
    def is_empty(self):
        return self.size == 0

    @property
    def is_completed(self):
        return self.size == 4

    @property
    def first_card(self):
        return self.cards[self.first_player_index]

    @property
    def lead_suit(self):
        return self.first_card.suit

    def add_card(self, player_index: int, card: Card):
        if self.is_empty:
            self.first_player_index = player_index
        self.cards[player_index] = card

    def reset(self):
        self.cards = [None, None, None, None]
        self.first_player_index = None


@dataclass
class CompletedTrick:
    cards: List[Card]
    first_player_index: int
    winner: int
    score: int
