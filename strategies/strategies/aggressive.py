from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState



class AggressiveStrategy(Strategy):
    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        # Play highest value card, preferring hearts and queen of spades
        return max(
            strategy_game_state.valid_moves,
            key=lambda card: card.rank + 13
            if (card.suit == "H" or card == Card.QueenOfSpades)
            else card.rank,
        )

