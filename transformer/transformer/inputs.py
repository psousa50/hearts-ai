from typing import List

import numpy as np
from hearts_game_core.game_models import GameCurrentState, Card
from tensorflow.keras.utils import to_categorical

CardToken = int

TRICK_SEPARATOR_TOKEN: CardToken = -1
COMPLETED_TRICK_SEPARATOR_TOKEN: CardToken = -2

# previous moves + 11 trick separators + 1 current trick separator
INPUT_SEQUENCE_LENGTH = 12 * (4 + 1) + 1 + 3
SUITS = ["C", "D", "H", "S"]


def pad_sequence(seq, length=INPUT_SEQUENCE_LENGTH):
    return [0] * (length - len(seq)) + seq


def card_token(card: Card):
    return SUITS.index(card.suit) * 13 + (card.rank - 2)


def card_from_token(card_idx: int) -> Card:
    return Card(suit=SUITS[card_idx // 13], rank=card_idx % 13 + 2)


def build_model_input(game_state: GameCurrentState):
    tokens = []
    for trick in game_state.previous_tricks:
        tokens.extend([card_token(card) for card in trick.ordered_cards()])
        tokens.append(TRICK_SEPARATOR_TOKEN)
    tokens.append(COMPLETED_TRICK_SEPARATOR_TOKEN)
    tokens.extend(
        [card_token(card) for card in game_state.current_trick.ordered_cards()]
    )
    tokens = pad_sequence(tokens)

    return tokens


def build_train_data(
    game_states: List[GameCurrentState], played_cards: List[Card]
) -> (np.ndarray, np.ndarray):
    X = [build_model_input(game_state) for game_state in game_states]
    y = [card_token(card) for card in played_cards]

    X = np.array(X)  # Convert list to NumPy array (N, INPUT_SEQUENCE_LENGTH)
    y = np.array(y)  # Convert list to NumPy array (N,)

    # One-hot encode the target values
    y_one_hot = to_categorical(y, num_classes=52)

    return X, y_one_hot
