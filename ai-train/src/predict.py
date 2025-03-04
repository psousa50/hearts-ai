from typing import List

from common import decode_card, encode_game_state
from model import Card, GameState


async def predict(model, state: GameState, valid_moves: List[Card] = None):
    print("State:", state)

    # Encode game state as sequence
    sequence = encode_game_state(
        gameState=state,
    )

    print("Sequence:", sequence)

    # Get model prediction
    prediction = model.predict(sequence.reshape(1, -1), verbose=0)

    print("Raw prediction:", prediction)

    prediction_cards = [
        (decode_card(card), idx) for card, idx in enumerate(prediction[0])
    ]
    sorted_prediction_cards = sorted(prediction_cards, key=lambda x: x[1], reverse=True)

    for p in sorted_prediction_cards[:5]:
        print(p)

    valid_prediction_cards = [p for p in sorted_prediction_cards if p[0] in valid_moves]

    chosen_move = valid_prediction_cards[0]
    return chosen_move[0]
