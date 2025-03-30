from hearts_game_core.game_models import Card
from hearts_game_core.random_manager import RandomManager
from hearts_game_core.strategies import Strategy, StrategyGameState


class RandomStrategy(Strategy):
    def __init__(self, random_manager: RandomManager = None):
        self.random_manager = random_manager or RandomManager()

    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        valid_moves = strategy_game_state.valid_moves
        if not valid_moves:
            # If no valid moves, return None (this shouldn't happen in a real game)
            return None

        return self.random_manager.choice(valid_moves)
