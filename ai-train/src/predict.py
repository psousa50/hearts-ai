from typing import Dict, List

from encoding import decode_card, encode_card, encode_game_state
from model import Card, GameState


async def predict(
    model, game_state: GameState, valid_moves: List[Card]
) -> Dict[str, any]:
    # Encode game state as sequence
    X, _ = encode_game_state(game_state)

    # Get model prediction for all cards
    prediction = model.predict(X.reshape(1, -1), verbose=0)[0]
    for p in prediction:
        card = decode_card(encode_card(p))
        print(f"{card}: {p}")

    # Filter prediction to only valid moves
    valid_indices = [encode_card(move) for move in valid_moves]
    valid_probs = prediction[valid_indices]
    best_valid_idx = valid_indices[valid_probs.argmax()]

    # Convert back to Card and return as dict
    chosen_card = decode_card(best_valid_idx)
    return {"suit": chosen_card.suit, "rank": chosen_card.rank}
