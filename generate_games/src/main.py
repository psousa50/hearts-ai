import argparse
import time
from dataclasses import dataclass

from hearts_game_core.game import Player
from hearts_game_core.game_core import HeartsGame

from strategies.strategies import (
    AggressiveStrategy,
    AvoidPointsStrategy,
    MyStrategy,
    RandomStrategy,
)


@dataclass
class PlayerStatistics:
    player_name: str
    strategy: str
    total_score: int
    total_wins: int


def main():
    parser = argparse.ArgumentParser(description="Train Hearts AI model on game data")
    parser.add_argument(
        "--num-games", type=int, default=1, help="Number of games to simulate"
    )
    parser.add_argument(
        "--same-deck",
        action="store_true",
        help="Use the same deck for all player positions (rotating players)",
    )

    args = parser.parse_args()

    print("Generating games...")

    players = [
        Player("Random", RandomStrategy()),
        Player("My Strategy", MyStrategy()),
        Player("AvoidPointsStrategy", AvoidPointsStrategy()),
        Player("AggressiveStrategy", AggressiveStrategy()),
    ]

    game_statistics = []
    for player in players:
        game_statistics.append(
            PlayerStatistics(
                player_name=player.name,
                strategy=player.strategy.__class__.__name__,
                total_score=0,
                total_wins=0,
            )
        )

    completed_games = []
    start_time = time.time()
    for _ in range(args.num_games):
        game = HeartsGame(players)
        completed_game = game.play_game()
        completed_games.append(completed_game)

        game_statistics[completed_game.winner_index].total_wins += 1
        for player_index, _ in enumerate(completed_game.players):
            game_statistics[player_index].total_score += completed_game.players[
                player_index
            ].score
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    display_statistics(args.num_games, game_statistics)


def display_statistics(num_games: int, game_statistics: list[PlayerStatistics]):
    sorted_statistics = sorted(
        game_statistics,
        key=lambda stat: stat.total_wins / len(game_statistics),
        reverse=True,
    )

    print("\nPlayer Statistics:")
    print(
        f"{'Player (Strategy)':<50} | {'Win Rate':^10} | {'Avg Score':^10} | {'Total Wins':^10}"
    )
    print("-" * 87)

    for game_stat in sorted_statistics:
        player_strategy = f"{game_stat.player_name} ({game_stat.strategy})"
        win_rate = f"{game_stat.total_wins / num_games * 100:.1f}%"
        avg_score = f"{game_stat.total_score / num_games:.1f}"
        total_wins = f"{game_stat.total_wins}"

        print(
            f"{player_strategy:<50} | {win_rate:^10} | {avg_score:^10} | {total_wins:^10}"
        )


if __name__ == "__main__":
    main()
