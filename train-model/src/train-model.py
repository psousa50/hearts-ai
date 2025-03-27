import argparse
import time
import copy
import datetime
from typing import List

import numpy as np
from hearts_game_core.game_core import CompletedGame, HeartsGame
from hearts_game_core.game_models import Card, Trick, GameCurrentState
from hearts_game_core.strategies import Player

from strategies.my import MyStrategy
from strategies.aggressive import AggressiveStrategy
from strategies.avoid_points import AvoidPointsStrategy
from strategies.random import RandomStrategy

from transformer.game_moves_filter import GameMovesFilter
from transformer.inputs import build_train_data, card_from_token, card_token
from transformer.transformer_model import HeartsTransformerModel

MODELS_DIR = "models"


def extract_training_data(
    completed_games: List[CompletedGame],
) -> (np.ndarray, np.ndarray):
    all_game_states = []
    all_played_cards = []
    for completed_game in completed_games:
        game_states, played_cards = extract_game_state_and_played_card(completed_game)
        all_game_states.extend(game_states)
        all_played_cards.extend(played_cards)
    return build_train_data(all_game_states, all_played_cards)


def extract_game_state_and_played_card(
    completed_game: CompletedGame,
) -> (List[GameCurrentState], List[Card]):
    games_filter = GameMovesFilter(completed_game)
    game_states = []
    played_cards = []
    for trick_index, trick in enumerate(completed_game.completed_tricks):
        previous_tricks = completed_game.completed_tricks[:trick_index]
        current_trick = Trick()
        for p in range(4):
            player_index = (trick.first_player_index + p) % 4
            played_card = trick.cards[player_index]
            if True or games_filter.filter(player_index, trick):
                game_state = GameCurrentState(
                    previous_tricks=previous_tricks,
                    current_trick=copy.deepcopy(current_trick),
                    current_player_index=player_index,
                )
                game_states.append(game_state)
                played_cards.append(played_card)

            current_trick.add_card(player_index, played_card)

    return game_states, played_cards


def game_moves_generator(batch_size: int):
    players = [
        Player("Random", RandomStrategy()),
        Player("My Strategy", MyStrategy()),
        Player("AvoidPointsStrategy", AvoidPointsStrategy()),
        Player("AggressiveStrategy", AggressiveStrategy()),
    ]
    generated_moves_count = 0
    while True:
        completed_game = HeartsGame(players).play_game()
        games_filter = GameMovesFilter(completed_game)
        game_states = []
        played_cards = []
        for trick_index, trick in enumerate(completed_game.completed_tricks):
            previous_tricks = completed_game.completed_tricks[:trick_index]
            current_trick = Trick()
            for p in range(4):
                player_index = (trick.first_player_index + p) % 4
                played_card = trick.cards[player_index]
                if games_filter.filter(player_index, trick):
                    game_state = GameCurrentState(
                        previous_tricks=previous_tricks,
                        current_trick=current_trick,
                        current_player_index=player_index,
                    )
                    game_states.append(game_state)
                    played_cards.append(played_card)
                    generated_moves_count += 1
                    if generated_moves_count >= batch_size:
                        train_data = build_train_data(game_states, played_cards)
                        generated_moves_count = 0
                        game_states = []
                        played_cards = []
                        yield train_data

                current_trick.add_card(player_index, trick.cards[player_index])


def generate_games(num_games: int) -> List[CompletedGame]:
    players = [
        Player("Random", RandomStrategy()),
        Player("My Strategy", MyStrategy()),
        Player("AvoidPointsStrategy", AvoidPointsStrategy()),
        Player("AggressiveStrategy", AggressiveStrategy()),
    ]
    games = []
    for _ in range(num_games):
        game = HeartsGame(players)
        games.append(game.play_game())
    return games


def model_path(size: int):
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = f"{MODELS_DIR}/model_{timestamp}_{size}.keras"
    return path


def train_model():
    parser = argparse.ArgumentParser(description="Generate games for Hearts game")
    parser.add_argument(
        "--num-games", type=int, default=1, help="Number of games to generate"
    )
    parser.add_argument(
        "--epochs", type=int, default=50, help="Number of epochs for training"
    )
    parser.add_argument(
        "--batch-size", type=int, default=32, help="Batch size for training"
    )

    args = parser.parse_args()
    num_games = args.num_games
    epochs = args.epochs
    batch_size = args.batch_size

    transformer = HeartsTransformerModel()
    transformer.build()
    start = time.time()
    games = generate_games(num_games)
    print(f"Generated {len(games)} games in {time.time() - start} seconds")
    train_data = extract_training_data(games)
    transformer.train(
        train_data,
        epochs=epochs,
        batch_size=batch_size,
    )
    transformer.save(model_path(len(train_data[0])))
    transformer.save("models/latest.keras")


def test_predict():
    transformer = HeartsTransformerModel()
    transformer.load(f"{MODELS_DIR}/latest.keras")
    current_trick = Trick()
    game_state = GameCurrentState(
        previous_tricks=[],
        current_trick=current_trick,
        current_player_index=0,
    )
    predictions = transformer.predict(game_state)
    # print predicted cards with probabilities, ordered by probability
    ordered_predicted_cards = [
        (card_from_token(i), predictions[0][i])
        for i in np.argsort(predictions[0])[-52:][::-1]
    ]
    for card, prob in ordered_predicted_cards:
        print(f"{card}: {prob * 100:.2f}%")


if __name__ == "__main__":
    train_model()
    test_predict()
