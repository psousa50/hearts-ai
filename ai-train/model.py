import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, Dense, Concatenate
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
import json

def encode_card(card):
    """Create one-hot encoded vector for a single card"""
    suit_map = {'H': 0, 'D': 1, 'C': 2, 'S': 3}
    idx = (card['rank'] - 2) * 4 + suit_map[card['suit']]
    return idx

def get_valid_moves(current_trick_cards, previous_tricks):
    """Get a list of all cards that have been played"""
    played_cards = set()
    
    # Add cards from current trick
    for card, _ in current_trick_cards:
        played_cards.add((card['suit'], card['rank']))
    
    # Add cards from previous tricks
    for trick in previous_tricks:
        for card, _ in trick['cards']:
            played_cards.add((card['suit'], card['rank']))
    
    # Create valid moves mask (1 for unplayed cards)
    valid_moves = np.ones(52)
    for suit, rank in played_cards:
        idx = (rank - 2) * 4 + {'H': 0, 'D': 1, 'C': 2, 'S': 3}[suit]
        valid_moves[idx] = 0
    
    return valid_moves

def get_current_hand(current_trick_cards, previous_tricks):
    """Get the current hand based on unplayed cards"""
    # Start with all cards unplayed
    hand = np.ones(52)
    
    # Mark played cards as 0
    for card, _ in current_trick_cards:
        idx = encode_card(card)
        hand[idx] = 0
    
    for trick in previous_tricks:
        for card, _ in trick['cards']:
            idx = encode_card(card)
            hand[idx] = 0
    
    return hand

def build_model():
    """Build the model architecture"""
    # Input layers
    hand_input = Input(shape=(52,), name='hand_input')
    valid_moves_input = Input(shape=(52,), name='valid_moves_input')
    
    # Combine inputs
    combined = Concatenate()([hand_input, valid_moves_input])
    
    # Dense layers
    x = Dense(256, activation='relu')(combined)
    x = Dense(128, activation='relu')(x)
    x = Dense(64, activation='relu')(x)
    
    # Output layer (52 cards)
    predictions = Dense(52, activation='softmax', name='predictions')(x)
    
    # Create model
    model = Model(
        inputs=[hand_input, valid_moves_input],
        outputs=predictions
    )
    
    # Compile model
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def train_model(data_path: str, epochs: int = 100, batch_size: int = 32):
    """Train the model"""
    # Load training data
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Prepare training data
    X_hand = []
    X_valid = []
    y = []
    
    for example in data:
        # Get current hand and valid moves
        hand = get_current_hand(example['current_trick_cards'], example['previous_tricks'])
        valid_moves = get_valid_moves(example['current_trick_cards'], example['previous_tricks'])
        
        # One-hot encode target card
        target = np.zeros(52)
        card = example['played_card']
        idx = encode_card(card)
        target[idx] = 1
        
        X_hand.append(hand)
        X_valid.append(valid_moves)
        y.append(target)
    
    X_hand = np.array(X_hand)
    X_valid = np.array(X_valid)
    y = np.array(y)
    
    # Create model
    model = build_model()
    
    # Create directories if they don't exist
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Callbacks
    callbacks = [
        ModelCheckpoint(
            'models/model_epoch_{epoch:02d}.h5',
            save_best_only=True,
            monitor='accuracy'
        ),
        CSVLogger('logs/training_log.csv')
    ]
    
    # Train
    history = model.fit(
        [X_hand, X_valid],
        y,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        validation_split=0.2
    )
    
    # Save final model
    model.save('models/latest.h5')  # Using HDF5 format
    
    return history

if __name__ == '__main__':
    train_model('data/training_data_20250302_105143_10_games.json', epochs=10)
