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


def generate_training_data(num_games: int) -> (np.ndarray, np.ndarray):
    all_game_states = []
    all_best_moves = []
    
    for game_num in range(num_games):
        print(f"Generating game {game_num + 1}/{num_games}")
        # Create a game with random players
        players = [Player(f"Random{i}", RandomStrategy()) for i in range(4)]
        game = HeartsGame(players)
        
        # Play the game until completion, collecting training data at each step
        while not game.is_game_over():
            player_idx = game.current_player_index
            valid_moves = game.get_valid_moves(player_idx)
            
            best_move = None
            if len(valid_moves) > 0:  # Only simulate when there are choices to make
                # Save current game state for training data
                current_state = copy.deepcopy(game.current_state)
                
                # Simulate 100 games for each valid move to find the best one
                best_added_score = float('inf')
                
                print("-" * 50)
                print(f"Current trick: {" ".join(map(str, game.current_trick.cards))}")
                current_score = game.players[player_idx].score
                for move in valid_moves:
                    total_added_score = 0
                    num_simulations = 100
                    
                    for _ in range(num_simulations):
                        sim_game = copy.deepcopy(game)
                        
                        redistribute_cards(sim_game)
                        
                        sim_game.play_card(move)
                        
                        sim_completed_game = sim_game.play_game()
                        
                        player_score = sim_completed_game.players[player_idx].score
                        total_added_score += player_score - current_score
                    
                    avg_added_score = total_added_score / num_simulations
                    print(f"Simulated move {move}: {avg_added_score}")
                    if avg_added_score < best_added_score:
                        best_added_score = avg_added_score
                        best_move = move

                print(f"Best move for player {player_idx}: {best_move} (avg score: {best_added_score})")
                # Add the game state and best move to training data
                if avg_added_score < 0.1:
                    all_game_states.append(current_state)
                    all_best_moves.append(best_move)
            
            # Play the next card in the actual game (using random strategy)
            if best_move is None:
                game.play_next_card()
            else:
                game.play_card(best_move)

        print("Game Over")
        for player in game.players:
            print(f"Player {player.name}: {player.score}")
    
    # Build training data from collected game states and best moves
    return all_game_states, all_best_moves
    # return build_train_data(all_game_states, all_best_moves)


def redistribute_cards(game: HeartsGame):
    current_player_idx = game.current_player_index
    
    player_missing_suits = [set() for _ in range(4)]
    
    for trick in game.previous_tricks:
        lead_suit = trick.cards[trick.first_player_index].suit
        for player_idx in range(4):
            if trick.cards[player_idx].suit != lead_suit and player_idx != trick.first_player_index:
                player_missing_suits[player_idx].add(lead_suit)
    
    player_card_counts = [len(player.hand) for player in game.players]
    
    all_cards = []
    for player_idx, player in enumerate(game.players):
        if player_idx != current_player_idx:
            all_cards.extend(player.hand)
            player.hand = []
    
    # Shuffle all collected cards
    np.random.shuffle(all_cards)
    
    # Group remaining cards by suit for easier assignment
    remaining_cards = {"C": [], "D": [], "H": [], "S": []}
    for card in all_cards:
        remaining_cards[card.suit].append(card)
    
    # Assign cards to each player (except current player) up to their original count
    for player_idx in range(4):
        if player_idx == current_player_idx:
            continue  # Skip the current player
            
        cards_needed = player_card_counts[player_idx]
        
        # First try to assign cards the player can receive
        for suit in ["C", "D", "H", "S"]:
            if suit in player_missing_suits[player_idx]:
                continue  # Skip suits the player can't have
                
            # Take cards of this suit
            while cards_needed > 0 and remaining_cards[suit]:
                game.players[player_idx].hand.append(remaining_cards[suit].pop())
                cards_needed -= 1
                
        # If we still need cards, we'll have to break some constraints
        # This should rarely happen in a valid game
        if cards_needed > 0:
            # Collect all remaining cards
            all_remaining = []
            for suit_cards in remaining_cards.values():
                all_remaining.extend(suit_cards)
            
            # Take what we need
            for _ in range(min(cards_needed, len(all_remaining))):
                # Find the card in remaining_cards and remove it
                card = all_remaining.pop()
                remaining_cards[card.suit].remove(card)
                game.players[player_idx].hand.append(card)


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
    # train_model()
    # test_predict()
    game_states, best_moves = generate_training_data(1)
