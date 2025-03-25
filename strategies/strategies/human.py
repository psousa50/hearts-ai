from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState


class HumanStrategy(Strategy):
    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        raise NotImplementedError
