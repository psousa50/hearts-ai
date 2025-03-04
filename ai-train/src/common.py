import numpy as np
from model import Card, GameState


def encode_card(card: Card) -> int:
    """Create index for a single card (0-51)"""
    suit_map = {"H": 0, "D": 1, "C": 2, "S": 3}
    idx = (card.rank - 2) * 4 + suit_map[card.suit]
    return idx


def decode_card(idx: int) -> Card:
    """Decode index to a card"""
    suit_map = {0: "H", 1: "D", 2: "C", 3: "S"}
    rank = (idx // 4) + 2
    suit = suit_map[idx % 4]
    return Card(suit=suit, rank=rank)


def encode_game_state(gameState: GameState) -> np.ndarray:
    """
    Encode game state as a sequence of tokens:
    - First token: trick number (0-12) -> [0-12]
    - Second token: current player (0-3) -> [13-16]
    - For each previous trick:
        - 4 tokens for cards played (0-51) -> [17-68]
        - 1 token for winner (0-3) -> [69-72]
    - Current trick cards (0-51 or special "empty" token 52) -> [17-68] after previous tricks
    - Hand cards (0-51) -> after current trick
    """
    max_tricks: int = 13

    # Calculate token positions
    trick_number_offset = 0  # 0-12  # noqa: F841
    player_index_offset = 13  # 13-16
    cards_offset = 17  # 17-68 (52 possible cards)
    winner_offset = 69  # 69-72 (4 possible winners)
    empty_token = 52  # Special token for empty card slot

    # Initialize sequence with special padding token
    seq_length = 2  # trick_number + player_index
    seq_length += max_tricks * 5  # each trick has 4 cards + winner
    seq_length += 4  # current trick (up to 4 cards)
    seq_length += 13  # hand (up to 13 cards)

    sequence = np.full(seq_length, empty_token)

    # Add trick number and player index
    sequence[0] = gameState.trick_number
    sequence[1] = gameState.current_player_index + player_index_offset

    # Add previous tricks
    pos = 2
    for i, trick in enumerate(gameState.previous_tricks):
        if i >= max_tricks:
            break

        # Add cards
        for cardMove in trick.cards:
            sequence[pos] = encode_card(cardMove.card) + cards_offset
            pos += 1

        # Pad remaining cards in trick
        pos += 4 - len(trick.cards)

        # Add winner
        sequence[pos] = trick.winner + winner_offset
        pos += 1

    # Add current trick
    for cardMove in gameState.current_trick_cards:
        sequence[pos] = encode_card(cardMove.card) + cards_offset
        pos += 1

    # Add hand
    pos = seq_length - 13  # Last 13 positions reserved for hand
    for card in gameState.player_hand:
        sequence[pos] = encode_card(card) + cards_offset
        pos += 1

    return sequence
