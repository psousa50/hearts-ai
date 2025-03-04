from fastapi import FastAPI, HTTPException
import uvicorn
import logging
from predict import predict

from model import GameState, load_model

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
async def predict_post(state: GameState):
    try:
        logger.info("=" * 50)
        logger.info(f"Prediction request - Game: {state.game_id}, Trick: {state.trick_number}")
        logger.info(f"Hand: {state.hand}")
        logger.info(f"Valid moves: {state.valid_moves}")

        chosen_move = await predict(model, state)
        logger.info(f"Chosen move: {chosen_move}")
        logger.info("=" * 50)
        print("chosen move:", chosen_move)

        return chosen_move

    
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")