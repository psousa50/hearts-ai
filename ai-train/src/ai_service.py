import logging
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException
from model import Card, GameState, load_model
from predict import predict
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger("ai_service")
logger.setLevel(logging.INFO)

app = FastAPI()

logger.info("Starting AI service...")

# Load the model at startup
logger.info("Loading model...")
model = load_model("models/latest.keras")
model.summary()
logger.info("Model loaded successfully")


class PredictRequest(BaseModel):
    state: GameState
    valid_moves: List[Card]


@app.post("/predict")
async def predict_post(request: PredictRequest):
    print("Received prediction request:", request)
    try:
        logger.info("=" * 50)
        logger.info(
            f"Prediction request - Game: {request.state.game_id}, Trick: {request.state.trick_number}"
        )
        logger.info(f"Hand: {request.state.player_hand}")
        logger.info(f"Valid moves: {request.valid_moves}")

        chosen_move = await predict(model, request.state, request.valid_moves)
        logger.info(f"Chosen move: {chosen_move}")
        logger.info("=" * 50)
        print("chosen move:", chosen_move)

        return chosen_move

    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
