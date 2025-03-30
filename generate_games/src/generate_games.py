from hearts_game_core.deck import Deck
from hearts_game_core.game_models import CompletedGame
from hearts_game_core.game_core import HeartsGame
from hearts_game_core.strategies import Player

import argparse
import json
import os
import time
from dataclasses import dataclass

from strategies.aggressive import AggressiveStrategy
from strategies.avoid_points import AvoidPointsStrategy
from strategies.my import MyStrategy
from strategies.random import RandomStrategy
from strategies.ai import AIStrategy
from strategies.simulation import SimulationStrategy
from strategies.monte_carlo import MonteCarloStrategy

from hearts_game_core.random_manager import RandomManager


@dataclass
class PlayerStatistics:
    player_name: str
    strategy: str
    total_score: int
    total_wins: int


def generate_games():
    parser = argparse.ArgumentParser(description="Generate games for Hearts game")
    parser.add_argument(
        "--num-games", type=int, default=1, help="Number of games to generate"
    )
    parser.add_argument(
        "--same-deck",
        action="store_true",
        help="Use the same deck for all player positions (rotating players)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for random number generator",
    )

    args = parser.parse_args()
    num_games = args.num_games
    same_deck = args.same_deck
    seed = args.seed

    print(f"Generating {num_games} games with same deck: {same_deck} and seed: {seed}")
    
    random_manager = RandomManager(seed)
    players = [
        Player("My Strategy 1", MyStrategy()),
        Player("My Strategy 2", MyStrategy()),
        Player("Monte Carlo 1", MonteCarloStrategy(random_manager=random_manager)),
        Player("Sim 1", SimulationStrategy(random_manager=random_manager)),
    ]

    # players = [
    #     Player("Sim 1", SimulationStrategy()),
    #     Player("Sim 2", SimulationStrategy()),
    #     Player("Sim 3", SimulationStrategy()),
    #     Player("Sim 4", SimulationStrategy()),
    # ]

    print("Players:")
    for player in players:
        print(f"{player.name} ({player.strategy.__class__.__name__})")

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
    for i in range(num_games):
        print(f"Game {i + 1}/{num_games}")
        if (i % 4 == 0) or not same_deck:
            deck = Deck(random_manager=random_manager)
        else:
            deck.shift_left(13)
            
        game = HeartsGame(players, deck, random_manager=random_manager)
        completed_game = game.play_game()
        completed_games.append(completed_game)
        update_statistics(completed_game, game_statistics)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    display_statistics(num_games, game_statistics)

    save_completed_games(completed_games)


def save_completed_games(completed_games: list[CompletedGame]):
    os.makedirs("completed_games", exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    num_games = len(completed_games)
    filename = f"games_{timestamp}_{num_games}.json"
    with open(f"completed_games/{filename}", "w") as f:
        json.dump([game.model_dump() for game in completed_games], f)


def update_statistics(
    completed_game: CompletedGame, game_statistics: list[PlayerStatistics]
):
    game_statistics[completed_game.winner_index].total_wins += 1
    for player_index, _ in enumerate(completed_game.players):
        game_statistics[player_index].total_score += completed_game.players[
            player_index
        ].score


def display_statistics(num_games: int, game_statistics: list[PlayerStatistics]):
    sorted_statistics = sorted(
        game_statistics,
        # Sort by win rate (descending) and then by average score (ascending, since lower is better)
        key=lambda stat: (-stat.total_wins / num_games, stat.total_score / num_games)
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
    generate_games()
