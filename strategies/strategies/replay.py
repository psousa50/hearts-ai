import sys
from typing import List

from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState

DEBUG = False


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force output to be displayed immediately


class ReplayStrategy(Strategy):
    def __init__(self, cards: List[Card]):
        self.cards = cards.copy()  # Make a copy to avoid modifying the original
        self.current_index = 0

    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        debug_print("------------------------------------------------")
        debug_print(
            "Player hand:", [str(card) for card in strategy_game_state.player_hand]
        )
        debug_print("Cards:", [str(card) for card in self.cards])
        debug_print("Current trick:", strategy_game_state.game_state.current_trick)
        debug_print("Valid moves:", strategy_game_state.valid_moves)
        debug_print(
            "Current player:", strategy_game_state.game_state.current_player_index
        )

        if self.current_index >= len(self.cards):
            raise ValueError("Replay strategy ran out of cards")

        card = self.cards[self.current_index]
        self.current_index += 1

        # Verify the card is valid
        if card not in strategy_game_state.valid_moves:
            debug_print("Card not in valid moves:", card)
            raise ValueError("Replay strategy predicted invalid move")

        debug_print("Chosen card:", card)
        return card

    def reset(self):
        """Reset the replay sequence back to the start"""
        self.current_index = 0
