from typing import List

import numpy as np
from tensorflow import keras
from tensorflow.keras.utils import to_categorical

from hearts_game_core.game_models import Card, GameCurrentState

CardToken = int

PADDING_TOKEN: CardToken = 0
TRICK_SEPARATOR_TOKEN: CardToken = -1
COMPLETED_TRICK_SEPARATOR_TOKEN: CardToken = -2

TOKENS_DIM = 52 + 3

# previous tricks with a separator betwwen + 1 current trick separator + 3 trick cards
INPUT_LENGTH = 12 * 4 + 11 + 1 + 3
SUITS = ["C", "D", "H", "S"]
NUM_CARDS = 52


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

    return tokens


def map_tokens(sequences):
    # Shift card values from 0-51 to 1-52
    if not isinstance(sequences, np.ndarray):
        sequences = np.array(sequences, dtype=np.int32)

    # Create a copy to avoid modifying the original array
    mapped_sequences = sequences.copy()

    # Mask for valid card values (0-51)
    valid_card_mask = (mapped_sequences >= 0) & (mapped_sequences <= 51)

    # Map card values (0-51 → 1-52)
    mapped_sequences[valid_card_mask] += 1

    # Map special tokens
    mapped_sequences[mapped_sequences == -1] = 53
    mapped_sequences[mapped_sequences == -2] = 54

    return mapped_sequences


def build_train_data(
    game_states: List[GameCurrentState], played_cards: List[Card]
) -> (np.ndarray, np.ndarray):
    X = [build_model_input(game_state) for game_state in game_states]
    X = [map_tokens(sequence) for sequence in X]
    X = keras.preprocessing.sequence.pad_sequences(
        X, maxlen=INPUT_LENGTH, padding="post", truncating="post"
    )

    y = [card_token(card) for card in played_cards]
    y = np.array(y)

    y = to_categorical(y, num_classes=NUM_CARDS)

    return X, y
