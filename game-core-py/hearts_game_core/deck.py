from hearts_game_core.game_models import Card
import random
from typing import List


class Deck:
    def __init__(self):
        self.cards = []
        self.reset()

    def reset(self):
        self.cards = [
            Card(suit=suit, rank=rank)
            for suit in "SHDC"
            for rank in range(2, 15)
        ]
        random.shuffle(self.cards)

    def shift_left(self, num_cards: int):
        self.cards = self.cards[num_cards:] + self.cards[:num_cards]    
        

    def deal(self, num_hands: int, num_cards: int) -> List[List[Card]]:
        hands = [self.cards[s * num_cards:(s + 1) * num_cards] for s in range(0, num_hands)]
        return hands
