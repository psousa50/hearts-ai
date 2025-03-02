from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import tensorflow as tf
import numpy as np
import uvicorn

app = FastAPI()

# Load the model at startup using TFSMLayer for Keras 3
model = tf.keras.layers.TFSMLayer('models/latest', call_endpoint='serving_default')

class GameState(BaseModel):
    hand: List[Tuple[str, int]]  # List of (suit, rank) tuples
    valid_moves: List[Tuple[str, int]]  # List of (suit, rank) tuples

def encode_cards(cards: List[dict]) -> np.ndarray:
    """Create one-hot encoded vector for cards"""
    encoding = np.zeros(52)
    for card in cards:
        suit_map = {'H': 0, 'D': 1, 'C': 2, 'S': 3}
        index = (card['rank'] - 2) * 4 + suit_map[card['suit']]
        encoding[index] = 1
    return encoding

@app.post("/predict")
async def predict(state: GameState):
    try:
        # Convert tuples to card dicts
        hand = [{'suit': suit, 'rank': rank} for suit, rank in state.hand]
        valid_moves = [{'suit': suit, 'rank': rank} for suit, rank in state.valid_moves]
        
        # Encode cards using same logic as training
        hand_encoded = encode_cards(hand)
        valid_moves_encoded = encode_cards(valid_moves)
        
        # Get model prediction using the layer's call method
        inputs = {
            'hand_input': hand_encoded.reshape(1, -1),
            'valid_moves_input': valid_moves_encoded.reshape(1, -1)
        }
        prediction = model(inputs)['predictions']
        
        # Find the valid move with highest prediction score
        best_move_idx = 0
        best_score = float('-inf')
        
        for i, move in enumerate(valid_moves):
            suit_map = {'H': 0, 'D': 1, 'C': 2, 'S': 3}
            card_idx = (move['rank'] - 2) * 4 + suit_map[move['suit']]
            score = prediction[0][card_idx]
            if score > best_score:
                best_score = score
                best_move_idx = i
        
        chosen_move = state.valid_moves[best_move_idx]
        return {"suit": chosen_move[0], "rank": chosen_move[1]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)