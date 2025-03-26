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
            card_from_token(i)
            for i in np.argsort(predictions[0])[-52:][::-1]
        ]
        for card in ordered_predicted_cards:
            if card in strategy_game_state.valid_moves:
                debug_print(f"Chosen card: {card}")
                return card
        raise ValueError("No valid moves predicted")
