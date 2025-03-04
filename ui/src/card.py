from dataclasses import dataclass

@dataclass
class Card:
    suit: str
    rank: int

    def __str__(self):
        return f"{self.rank}{self.suit}"

