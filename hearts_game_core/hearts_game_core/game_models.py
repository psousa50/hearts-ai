from dataclasses import dataclass, field
from typing import ClassVar, List, Optional

from pydantic import BaseModel


class Card(BaseModel):
    suit: str
    rank: int

    def json(self, **kwargs):
        return super().model_dump_json(**kwargs)

    def __str__(self):
        return f"{self.rank}{self.suit}"


Card.QueenOfSpades: ClassVar[Card] = Card(suit="S", rank=12)
Card.TwoOfClubs: ClassVar[Card] = Card(suit="C", rank=2)


class Trick(BaseModel):
    cards: List[Optional[Card]] = [None, None, None, None]
    first_player_index: int = 0

    def __post_init__(self):
        self.reset()

    def __str__(self):
        return (
            " ".join([str(card) for card in self.all_cards()])
            if not self.is_empty
            else "(No Cards)"
        )

    def json(self, **kwargs):
        return super().model_dump_json(**kwargs)

    @property
    def size(self):
        return len([card for card in self.cards if card is not None])

    @property
    def is_empty(self):
        return self.cards.count(None) == 4

    @property
    def is_completed(self):
        return self.cards.count(None) == 0

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
        self.first_player_index = 0

    def score(self):
        s = 0
        for card in self.all_cards():
            if card.suit == "H":
                s += 1
            if card == Card.QueenOfSpades:
                s += 13
        return s

    def all_cards(self):
        return [card for card in self.cards if card is not None]

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
    winner_index: int
    score: int

    def json(self, **kwargs):
        return super().model_dump_json(**kwargs)

    def ordered_cards(self):
        return [
            card
            for card in (
                self.cards[self.first_player_index :]
                + self.cards[: self.first_player_index]
            )
        ]

@dataclass
class GameCurrentState:
    previous_tricks: List[CompletedTrick] = field(default_factory=list)
    current_trick: Trick = field(default_factory=Trick)
    hearts_broken: bool = False
    current_player_index: int = -1

    def reset(self):
        self.previous_tricks = []
        self.current_trick.reset()
        self.hearts_broken = False
        self.current_player_index = -1

    def set_first_player(self, player_index: int):
        self.current_player_index = player_index
        self.current_trick.first_player_index = player_index


class PlayerInfo(BaseModel):
    name: str
    strategy: str
    initial_hand: List[Card] = []
    score: int


class CompletedGame(BaseModel):
    players: List[PlayerInfo]
    winner_index: int
    completed_tricks: List[CompletedTrick]
