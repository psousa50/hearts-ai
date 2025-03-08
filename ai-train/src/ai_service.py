import logging
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException
from model_builder import load_model
from predict import predict
from predict_request import PredictRequest
from pydantic import parse_obj_as

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


@app.post("/predict")
async def predict_post(request: dict):
    print("Received prediction request:", request)
    predictRequest = PredictRequest.model_validate(request)

    print("Received prediction request:", predictRequest)
    try:
        logger.info("=" * 50)
        logger.info(f"Prediction request - Game: {predictRequest.state}")
        logger.info(f"Hand: {predictRequest.state.player_hand}")
        logger.info(f"Valid moves: {predictRequest.valid_moves}")

        chosen_move = await predict(
            model, predictRequest.state, predictRequest.valid_moves
        )
        logger.info(f"Chosen move: {chosen_move}")
        logger.info("=" * 50)
        print("chosen move:", chosen_move)

        return chosen_move

    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
