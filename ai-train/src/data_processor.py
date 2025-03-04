import numpy as np
from typing import Dict, List, Tuple
from sklearn.model_selection import train_test_split
import json

def encode_card(card: Dict) -> str:
    """Encode a card into a token string"""
    return f"RANK_{card['rank']}_SUIT_{card['suit']}"

def process_game_state(game_state: Dict, game_tokens: Dict[str, int], max_seq_length: int) -> np.ndarray:
    """Convert game state into model input format"""
    sequence = []
    
    # Add START token
    sequence.append(game_tokens['START'])
    
    # Add previous tricks
    for trick in game_state['previous_tricks']:
        sequence.append(game_tokens['TRICK_START'])
        for card, _ in trick['cards']:
            sequence.append(game_tokens[f"RANK_{card['rank']}_SUIT_{card['suit']}"])
        sequence.append(game_tokens['TRICK_END'])
    
    # Add current trick cards
    sequence.append(game_tokens['TRICK_START'])
    for card, _ in game_state['current_trick_cards']:
        sequence.append(game_tokens[f"RANK_{card['rank']}_SUIT_{card['suit']}"])
    sequence.append(game_tokens['TRICK_END'])
    
    # Add END token
    sequence.append(game_tokens['END'])
    
    # Pad sequence
    while len(sequence) < max_seq_length:
        sequence.append(game_tokens['PAD'])
    
    sequence = sequence[:max_seq_length]  # Truncate if too long
    return np.array(sequence)

def encode_target_card(card: Dict) -> np.ndarray:
    """Create one-hot encoded vector for target card"""
    target = np.zeros(52)
    # Calculate index based on rank and suit
    # Ranks: 2-14 (13 ranks), Suits: H,D,C,S (4 suits)
    suit_map = {'H': 0, 'D': 1, 'C': 2, 'S': 3}
    index = (card['rank'] - 2) * 4 + suit_map[card['suit']]
    target[index] = 1
    return target

def load_training_data(data_path: str) -> List[Dict]:
    """Load training data from JSON file"""
    with open(data_path, 'r') as f:
        return json.load(f)

def process_game_data(data_path: str, game_tokens: Dict[str, int], max_seq_length: int,
                     test_size: float = 0.2) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Process game data into training and validation sets"""
    training_items = load_training_data(data_path)
    X_data = []
    y_data = []
    
    for item in training_items:
        # Create game state dictionary from training item
        game_state = {
            'previous_tricks': item['previous_tricks'],
            'current_trick_cards': item['current_trick_cards']
        }
        
        # Process game state into model input format
        X = process_game_state(game_state, game_tokens, max_seq_length)
        # Create target vector for the played card
        y = encode_target_card(item['played_card'])
        
        X_data.append(X)
        y_data.append(y)
    
    X_data = np.array(X_data)
    y_data = np.array(y_data)
    
    # Split into training and validation sets
    X_train, X_val, y_train, y_val = train_test_split(
        X_data, y_data, test_size=test_size, random_state=42
    )
    
    return X_train, y_train, X_val, y_val
