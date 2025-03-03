from typing import List, Dict, Any, Tuple, Union
import numpy as np

def encode_card(card: Dict[str, Any]) -> int:
    """Create index for a single card (0-51)"""
    suit_map = {'H': 0, 'D': 1, 'C': 2, 'S': 3}
    idx = (card['rank'] - 2) * 4 + suit_map[card['suit']]
    return idx

def encode_game_state(
    trick_number: int,
    current_player_index: int,
    previous_tricks: List[Dict[str, Any]],
    hand: List[Dict[str, Any]],
    current_trick_cards: List[Tuple[Dict[str, Any], int]],
    max_tricks: int = 13,
) -> np.ndarray:
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
    # Calculate token positions
    trick_number_offset = 0  # 0-12
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
    sequence[0] = trick_number
    sequence[1] = current_player_index + player_index_offset
    
    # Add previous tricks
    pos = 2
    for i, trick in enumerate(previous_tricks):
        if i >= max_tricks:
            break
            
        # Add cards
        for card, player_idx in trick['cards']:
            sequence[pos] = encode_card(card) + cards_offset
            pos += 1
            
        # Pad remaining cards in trick
        pos += 4 - len(trick['cards'])
        
        # Add winner
        sequence[pos] = trick['winner'] + winner_offset
        pos += 1
    
    # Add current trick
    for card, _ in current_trick_cards:
        sequence[pos] = encode_card(card) + cards_offset
        pos += 1
    
    # Add hand
    pos = seq_length - 13  # Last 13 positions reserved for hand
    for card in hand:
        sequence[pos] = encode_card(card) + cards_offset
        pos += 1
    
    return sequence

def decode_card_token(token: int) -> Dict[str, Any]:
    """Convert a card token back to a card dict"""
    if token < 17 or token > 68:  # Not a card token
        return None
        
    card_idx = token - 17  # Remove offset
    rank = (card_idx // 4) + 2
    suit_map = {0: 'H', 1: 'D', 2: 'C', 3: 'S'}
    suit = suit_map[card_idx % 4]
    
    return {'suit': suit, 'rank': rank}

def get_hand_vector(cards: List[Dict[str, Any]]) -> np.ndarray:
    """Convert list of cards to one-hot encoded vector"""
    hand = np.zeros(52)
    for card in cards:
        idx = encode_card(card)
        hand[idx] = 1
    return hand

def get_trick_vector(trick_cards: List[Tuple[Dict[str, Any], int]], num_players: int = 4) -> np.ndarray:
    """Convert a trick's cards to a vector with card indices and player positions"""
    # For each position (0-3), we have a one-hot vector for the card played (52 dims) 
    # If no card played in that position, all zeros
    trick = np.zeros(num_players * 52)
    
    for card, player_idx in trick_cards:
        card_idx = encode_card(card)
        # Set the card in the player's position
        trick[player_idx * 52 + card_idx] = 1
    
    return trick

def get_previous_tricks_vector(previous_tricks: List[Dict[str, Any]], max_tricks: int = 13, num_players: int = 4) -> np.ndarray:
    """Convert previous tricks to a vector with cards played and winners"""
    # For each previous trick (max 13):
    # - Cards played (4 players * 52 cards = 208 dims)
    # - Winner (4 dims one-hot)
    trick_dims = num_players * 52 + num_players
    tricks = np.zeros(max_tricks * trick_dims)
    
    for i, trick in enumerate(previous_tricks):
        if i >= max_tricks:
            break
            
        # Encode cards played
        cards_vector = get_trick_vector(trick['cards'], num_players)
        tricks[i * trick_dims : i * trick_dims + num_players * 52] = cards_vector
        
        # Encode winner
        winner_start = i * trick_dims + num_players * 52
        tricks[winner_start + trick['winner']] = 1
    
    return tricks

def get_valid_moves(current_trick_cards: Union[List[Tuple[str, int]], List[Tuple[Dict[str, Any], int]]], previous_tricks: List[Dict[str, Any]]) -> np.ndarray:
    """Get a list of all cards that have been played"""
    played_cards = set()
    
    # Add cards from current trick
    for card_data, _ in current_trick_cards:
        # Handle both tuple and dict formats
        if isinstance(card_data, dict):
            suit, rank = card_data['suit'], card_data['rank']
        else:
            suit, rank = card_data
        played_cards.add((suit, rank))
    
    # Add cards from previous tricks
    for trick in previous_tricks:
        for card_data, _ in trick['cards']:
            # Handle both tuple and dict formats
            if isinstance(card_data, dict):
                suit, rank = card_data['suit'], card_data['rank']
            else:
                suit, rank = card_data
            played_cards.add((suit, rank))
    
    # Create valid moves mask (1 for unplayed cards)
    valid_moves = np.ones(52)
    for suit, rank in played_cards:
        suit_map = {'H': 0, 'D': 1, 'C': 2, 'S': 3}
        idx = (rank - 2) * 4 + suit_map[suit]
        valid_moves[idx] = 0
    
    return valid_moves
