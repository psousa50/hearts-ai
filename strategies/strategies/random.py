from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState
from hearts_game_core.random_manager import RandomManager

class RandomStrategy(Strategy):
    def __init__(self, random_manager: RandomManager = None):
        self.random_manager = random_manager or RandomManager()
    
    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
            
        return self.random_manager.choice(strategy_game_state.valid_moves)
