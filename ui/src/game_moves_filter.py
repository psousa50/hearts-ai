from typing import List

from card import CompletedTrick
from hearts_game import HeartsGame


class GameMovesFilter:
    def __init__(self, completed_game: HeartsGame):
        percentile25 = 1.25
        ordered_scores = sorted(completed_game.scores)
        threshold = (
            ordered_scores[0] + (ordered_scores[1] - ordered_scores[0]) * percentile25
        )
        self.good_players = [
            i for i, score in enumerate(completed_game.scores) if score <= threshold
        ]
        print(f"Good players: {self.good_players}")
        print(f"Threshold: {threshold}")
        print(f"Scores: {completed_game.scores}")

    def filter(self, player_index: int, trick: CompletedTrick) -> bool:
        return player_index in self.good_players and (
            trick.score <= 1 or trick.winner_index != player_index
        )
