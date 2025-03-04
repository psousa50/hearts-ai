from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
import tensorflow as tf
import numpy as np
import uvicorn
import logging

from common import encode_card, encode_game_state, decode_card_token

# Configure logging
logger = logging.getLogger("ai_service")
logger.setLevel(logging.INFO)

app = FastAPI()

logger.info("Starting AI service...")

# Load the model at startup
logger.info("Loading model...")
model = tf.keras.models.load_model('models/latest.keras')
model.summary()
logger.info("Model loaded successfully")

class TrainingTrick(BaseModel):
    cards: List[Tuple[str, int]]
    winner: int

class GameState(BaseModel):
    game_id: int
    trick_number: int
    previous_tricks: List[TrainingTrick]
    current_trick_cards: List[Tuple[str, int]]
    current_player_index: int
    hand: List[Tuple[str, int]]
    valid_moves: List[Tuple[str, int]]

@app.post("/predict")
async def predict(state: GameState):
    try:
        logger.info("=" * 50)
        logger.info(f"Prediction request - Game: {state.game_id}, Trick: {state.trick_number}")
        logger.info(f"Hand: {state.hand}")
        logger.info(f"Valid moves: {state.valid_moves}")
        
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
            hand=hand,
            current_trick_cards=current_trick,
        )
        
        # Get model prediction
        prediction = model.predict(
            sequence.reshape(1, -1),
            verbose=0
        )

        print("Raw prediction:", prediction)
        
        # Find the valid move with highest prediction score among valid moves
        best_move_idx = 0
        best_score = float('-inf')
        
        for i, move in enumerate(state.valid_moves):
            suit, rank = move
            card = {'suit': suit, 'rank': rank}
            # Use raw card index (0-51) instead of token (17-68)
            card_idx = encode_card(card)  # This gives us 0-51 index
            score = prediction[0][card_idx]
            if score > best_score:
                best_score = score
                best_move_idx = i

        print("Best card index:", card_idx)
        print("Best score:", best_score)
        
        chosen_move = state.valid_moves[best_move_idx]
        logger.info(f"Chosen move: {chosen_move}")
        logger.info("=" * 50)
        print("chosen move:", chosen_move)
        return {"suit": chosen_move[0], "rank": chosen_move[1]}
    
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")