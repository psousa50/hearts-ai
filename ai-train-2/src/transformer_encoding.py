from typing import List

import numpy as np
from game_classes import Card, GameState
from tensorflow.keras.utils import to_categorical

INPUT_SEQUENCE_LENGTH = 52  # Max number of past moves considered
SUITS = ["C", "D", "H", "S"]


def pad_sequence(seq, length=INPUT_SEQUENCE_LENGTH):
    return [0] * (length - len(seq)) + seq


def encode_card(card: Card):
    return SUITS.index(card.suit) * 13 + (card.rank - 2)


def decode_card(card_idx: int) -> Card:
    return Card(suit=SUITS[card_idx // 13], rank=card_idx % 13 + 2)


def build_input_sequence(game_state: GameState) -> np.ndarray:
    previous_moves = []
    for trick in game_state.previous_tricks:
        previous_moves.extend([encode_card(card) for card in trick.ordered_cards()])
    previous_moves.extend(
        [encode_card(card) for card in game_state.current_trick.ordered_cards()]
    )
    previous_moves = pad_sequence(previous_moves)

    X = np.array(previous_moves, dtype=np.int32).reshape(INPUT_SEQUENCE_LENGTH)
    return X


def build_train_data(game_states: List[GameState]) -> (np.ndarray, np.ndarray):
    X = []
    y = []

    for game_state in game_states:
        X.append(build_input_sequence(game_state))  # Encode input sequence
        y.append(encode_card(game_state.played_card))  # Encode output card

    X = np.array(X)  # Convert list to NumPy array (N, INPUT_SEQUENCE_LENGTH)
    y = np.array(y)  # Convert list to NumPy array (N,)

    # One-hot encode the target values
    y_one_hot = to_categorical(y, num_classes=52)

    return X, y_one_hot
