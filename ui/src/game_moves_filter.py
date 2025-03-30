from hearts_game_core.game_core import CompletedTrick
from hearts_game_core.game_models import CompletedGame


class GameMovesFilter:
    def __init__(self, completed_game: CompletedGame):
        percentile25 = 1.25
        scores = [player.score for player in completed_game.players]
        ordered_scores = sorted(scores)
        threshold = (
            ordered_scores[0] + (ordered_scores[1] - ordered_scores[0]) * percentile25
        )
        self.good_players = [i for i, score in enumerate(scores) if score <= threshold]
        print(f"Good players: {self.good_players}")
        print(f"Threshold: {threshold}")
        print(f"Scores: {scores}")

    def filter(self, player_index: int, trick: CompletedTrick) -> bool:
        return player_index in self.good_players and (
            trick.score <= 1 or trick.winner_index != player_index
        )
