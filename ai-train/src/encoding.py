from typing import List

import numpy as np
from model import Card, GameState, Trick

INPUT_SEQUENCE_LENGTH = 3173

# --- Encode suit as one-hot ---
SUITS = ["C", "D", "H", "S"]  # Clubs, Diamonds, Hearts, Spades
TOTAL_CARDS_PER_SUIT = 13
TOTAL_CARDS = TOTAL_CARDS_PER_SUIT * len(SUITS)

# --- Helper Functions ---


def one_hot_trick_number(trick_number: int) -> np.ndarray:
    one_hot = np.zeros(13)
    one_hot[trick_number] = 1
    return one_hot


def encode_card(card: Card) -> int:
    """Return the index of the card in a 52-card deck."""
    return SUITS.index(card.suit) * TOTAL_CARDS_PER_SUIT + (card.rank - 2)


def decode_card(idx: int) -> Card:
    """Decode index to a card"""
    suit = SUITS[idx // TOTAL_CARDS_PER_SUIT]
    rank = (idx % TOTAL_CARDS_PER_SUIT) + 2
    return Card(suit=suit, rank=rank)


def one_hot_card(card: Card) -> np.ndarray:
    """Return a 52-dimensional one-hot encoded vector for a card."""
    one_hot = np.zeros(TOTAL_CARDS)
    one_hot[encode_card(card)] = 1
    return one_hot


def one_hot_player(player_index: int) -> np.ndarray:
    """One-hot encode a player index (0-3)."""
    one_hot = np.zeros(4)
    one_hot[player_index] = 1
    return one_hot


def encode_trick(trick: Trick) -> np.ndarray:
    """Encode a trick with up to 4 moves (pad with zeros if fewer)."""
    trick_vector = np.zeros(4 * (TOTAL_CARDS + 4 + 4))  # (Card + Player + Winner) * 4
    for i, move in enumerate(trick.cards):
        card_vec = one_hot_card(move.card)
        player_vec = one_hot_player(move.player_index)
        winner_vec = one_hot_player(trick.winner)
        trick_vector[i * (TOTAL_CARDS + 4 + 4) : (i + 1) * (TOTAL_CARDS + 4 + 4)] = (
            np.concatenate([card_vec, player_vec, winner_vec])
        )
    return trick_vector


def encode_hand(hand: List[Card]) -> np.ndarray:
    """Encode player hand as a 52-dim vector (1 if card is in hand, 0 otherwise)."""
    hand_vector = np.zeros(TOTAL_CARDS)
    for card in hand:
        hand_vector[encode_card(card)] = 1
    return hand_vector


def encode_game_state(game_state: GameState) -> (np.ndarray, np.ndarray):
    """Convert GameState to feature vector (X) and output vector (y)."""

    trick_number = one_hot_trick_number(game_state.trick_number)

    # Encode last 12 tricks (pad if fewer)
    previous_tricks = np.zeros(12 * 4 * (TOTAL_CARDS + 4 + 4))  # (12 max tricks)
    for i, trick in enumerate(game_state.previous_tricks[-12:]):  # Last 12
        previous_tricks[
            i * 4 * (TOTAL_CARDS + 4 + 4) : (i + 1) * 4 * (TOTAL_CARDS + 4 + 4)
        ] = encode_trick(trick)

    # Encode current trick cards (up to 4)
    current_trick = np.zeros(4 * (TOTAL_CARDS + 4))
    for i, move in enumerate(game_state.current_trick):
        card_vec = one_hot_card(move.card)
        player_vec = one_hot_player(move.player_index)
        current_trick[i * (TOTAL_CARDS + 4) : (i + 1) * (TOTAL_CARDS + 4)] = (
            np.concatenate([card_vec, player_vec])
        )

    # Encode current player
    current_player = one_hot_player(game_state.current_player_index)

    # Encode player hand
    hand_vector = encode_hand(game_state.player_hand)

    # Concatenate all feature vectors
    X = np.concatenate(
        [trick_number, previous_tricks, current_trick, current_player, hand_vector]
    )

    # Encode output (played card as one-hot)
    y = one_hot_card(game_state.played_card) if game_state.played_card else None

    # print_one_hot("Trick Number", trick_number)
    # print_one_hot("Previous Tricks", previous_tricks)
    # print_one_hot("Current Trick", current_trick)
    # print_one_hot("Current Player", current_player)
    # print_one_hot("Hand Vector", hand_vector)
    # print_one_hot("Played Card", y)

    return X, y


def print_one_hot(title: str, one_hot: np.ndarray):
    if one_hot is None:
        print(f"{title}: None")
        return
    print(f"{title}: {one_hot.shape}")
    for i, value in enumerate(one_hot):
        if value == 1:
            print(i)
