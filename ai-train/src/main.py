import asyncio

import numpy as np
from encoding import decode_card, encode_game_state
from model import Card, CardMove, GameState, Trick, load_model
from predict import predict


def create_game_state():
    state = GameState(
        game_id=0,
        trick_number=1,
        previous_tricks=[
            Trick(
                cards=[
                    CardMove(card=Card(suit="C", rank=5), player_index=0),
                    CardMove(card=Card(suit="D", rank=6), player_index=1),
                    CardMove(card=Card(suit="S", rank=7), player_index=2),
                    CardMove(card=Card(suit="H", rank=8), player_index=3),
                ],
                winner=3,
            )
        ],
        current_trick=[
            CardMove(card=Card(suit="S", rank=2), player_index=0),
            CardMove(card=Card(suit="D", rank=3), player_index=1),
            CardMove(card=Card(suit="D", rank=4), player_index=2),
        ],
        current_player_index=3,
        player_hand=[
            Card(suit="D", rank=2),
            Card(suit="D", rank=3),
            Card(suit="D", rank=4),
            Card(suit="S", rank=5),
            Card(suit="S", rank=12),
        ],
        played_card=Card(suit="S", rank=14),
    )
    return state


def test_encode():
    state = create_game_state()
    X, y = encode_game_state(state)
    best_card_index = np.argmax(y)
    card = decode_card(best_card_index)
    print(card)


async def test_predict(model):
    state = create_game_state()
    valid_moves = [
        Card(suit="S", rank=12),
        Card(suit="C", rank=13),
        Card(suit="S", rank=5),
    ]
    chosen_move = await predict(model, state, valid_moves)
    print("chosen move:", chosen_move)


if __name__ == "__main__":
    model = load_model("models/latest.keras")
    asyncio.run(test_predict(model))
    # test_encode()
