import logging
from typing import List

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from game_classes import Card, GameState
from pydantic import BaseModel
from transformer_encoding import decode_card
from transformer_model import HeartsTransformerModel


class PredictRequest(BaseModel):
    state: GameState
    valid_moves: List[Card]


# Configure logging
logger = logging.getLogger("ai_service")
logger.setLevel(logging.INFO)

app = FastAPI()

logger.info("Starting AI service...")

# Load the model at startup
logger.info("Loading model...")
model = HeartsTransformerModel()
model.load("models/latest.keras")
logger.info("Model loaded successfully")


@app.post("/predict")
async def predict_post(request: dict):
    predictRequest = PredictRequest.model_validate(request)

    try:
        logger.info("=" * 50)
        logger.info(f"Prediction request - Game: {predictRequest.state}")
        logger.info(f"Hand: {predictRequest.state.player_hand}")
        logger.info(f"Valid moves: {predictRequest.valid_moves}")

        predictions = model.predict(predictRequest.state)
        ordered_predicted_cards = [
            decode_card(i) for i in np.argsort(predictions[0])[-52:][::-1]
        ]
        valid_predicted_cards = [
            card
            for card in ordered_predicted_cards
            if card in predictRequest.valid_moves
        ]
        print("\nTop most probable cards:")
        for card in valid_predicted_cards[:5]:
            print(f"Card: {card}")
        chosen_valid_move = valid_predicted_cards[0]

        logger.info(f"Chosen move: {chosen_valid_move}")

        return chosen_valid_move

    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
