from typing import List

import numpy as np
from predict_request import Card, GameState

INPUT_SEQUENCE_LENGTH = 13  # Number of past moves considered
SUITS = ["C", "D", "H", "S"]


def pad_sequence(seq, length=INPUT_SEQUENCE_LENGTH):
    return [0] * (length - len(seq)) + seq


def encode_card(card: Card):
    return SUITS.index(card.suit) * 13 + (card.rank - 2)


def build_input_sequence(game_state: GameState) -> np.ndarray:
    # flatten previous tricks mvoes in the right order
    previous_moves = []
    for trick in game_state.previous_tricks:
        ordered_cards = []
        card_idx = trick.first_player_index
        for _ in range(4):
            ordered_cards.append(trick.cards[card_idx])
            card_idx = (card_idx + 1) % 4
        previous_moves.extend([encode_card(card) for card in ordered_cards])
    previous_moves = pad_sequence(previous_moves)

    X = np.array(previous_moves)
    return X


def build_train_data(game_states: List[GameState]) -> (np.ndarray, np.ndarray):
    X = []
    y = []

    for game_state in game_states:
        X.append(build_input_sequence(game_state))  # Encode input sequence
        y.append(encode_card(game_state.played_card))  # Encode output card

    X = np.array(X)  # Convert list to NumPy array (N, INPUT_SEQUENCE_LENGTH)
    y = np.array(y)  # Convert list to NumPy array (N,)

    return X, y
