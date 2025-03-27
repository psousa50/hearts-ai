from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState
from transformer.transformer_model import HeartsTransformerModel
from transformer.inputs import card_from_token
import numpy as np

DEBUG = False

def debug_print(message):
    if DEBUG:
        print(message)

class AIStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.model = HeartsTransformerModel()
        self.model.load("models/latest.keras")

    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        predictions = self.model.predict(strategy_game_state.game_state)
        
        ordered_predicted_cards = [
            (card_from_token(i), predictions[0][i])
            for i in np.argsort(predictions[0])[-52:][::-1]
        ]
        debug_print("\nTop most probable cards:")
        for card, prob in ordered_predicted_cards:
            debug_print(f"{card} -> {prob * 100:.2f}% {'*' if card in strategy_game_state.valid_moves else ''}")
        
        valid_predicted_cards = [
            (card, prob)
            for card, prob in ordered_predicted_cards
            if card in strategy_game_state.valid_moves
        ]
        # debug_print("\nTop most probable valid cards:")
        # for card, prob in valid_predicted_cards:
        #     debug_print(f"{card} -> {prob * 100:.2f}%")
        if valid_predicted_cards:
            # debug_print(f"Chosen card: {valid_predicted_cards[0][0]} with probability {valid_predicted_cards[0][1] * 100:.2f}%")
            return valid_predicted_cards[0][0]
        raise ValueError("No valid moves predicted")
