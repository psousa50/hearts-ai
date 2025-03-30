import sys
from typing import List, Optional

from hearts_game_core.game_models import Card
from hearts_game_core.random_manager import RandomManager

DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force output to be displayed immediately


class Deck:
    def __init__(
        self, shuffle: bool = True, random_manager: Optional[RandomManager] = None
    ):
        self.cards = [
            Card(suit=suit, rank=rank) for suit in "SHDC" for rank in range(2, 15)
        ]
        self.random_manager = (
            random_manager if random_manager is not None else RandomManager()
        )
        if shuffle:
            self.shuffle()

    def shuffle(self):
        self.random_manager.shuffle(self.cards)

    def shift_left(self, num_cards: int):
        self.cards = self.cards[num_cards:] + self.cards[:num_cards]

    def deal(self, num_hands: int, num_cards: int) -> List[List[Card]]:
        hands = [
            self.cards[s * num_cards : (s + 1) * num_cards] for s in range(0, num_hands)
        ]
        return hands
