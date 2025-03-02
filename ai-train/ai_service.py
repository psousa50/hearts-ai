from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
import tensorflow as tf
import numpy as np
import uvicorn

from common import encode_card, encode_game_state, decode_card_token

app = FastAPI()

# Load the model at startup
model = tf.keras.models.load_model('models/latest.keras')

class TrainingTrick(BaseModel):
    cards: List[Tuple[str, int]]  # List of (suit, rank) tuples
    winner: int

class GameState(BaseModel):
    game_id: int
    trick_number: int
    previous_tricks: List[TrainingTrick]
    current_trick_cards: List[Tuple[str, int]]  # List of (suit, rank) tuples
    current_player_index: int
    hand: List[Tuple[str, int]]  # List of (suit, rank) tuples
    valid_moves: List[Tuple[str, int]]  # List of (suit, rank) tuples

@app.post("/predict")
async def predict(state: GameState):
    try:
        # Convert tuples to card dicts
        hand = [{'suit': suit, 'rank': rank} for suit, rank in state.hand]
        current_trick = [({"suit": suit, "rank": rank}, idx) for idx, (suit, rank) in enumerate(state.current_trick_cards)]
        previous_tricks = [
            {
                "cards": [({"suit": suit, "rank": rank}, idx) for idx, (suit, rank) in enumerate(trick.cards)],
                "winner": trick.winner
            }
            for trick in state.previous_tricks
        ]
        
        # Encode game state as sequence
        sequence = encode_game_state(
            trick_number=state.trick_number,
            current_player_index=state.current_player_index,
            previous_tricks=previous_tricks,
            current_trick_cards=current_trick,
            hand=hand
        )
        
        # Get model prediction
        prediction = model.predict(
            sequence.reshape(1, -1),
            verbose=0
        )
        
        # Find the valid move with highest prediction score among valid moves
        best_move_idx = 0
        best_score = float('-inf')
        
        for i, move in enumerate(state.valid_moves):
            suit, rank = move
            card = {'suit': suit, 'rank': rank}
            card_idx = encode_card(card)
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