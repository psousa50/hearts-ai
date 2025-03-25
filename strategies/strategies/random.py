import random
from typing import List

from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState


class RandomStrategy(Strategy):
    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        return random.choice(strategy_game_state.valid_moves)


