import random

import numpy as np
from game_classes import Card, GameState, Trick
from transformer_encoding import decode_card
from transformer_model import HeartsTransformerModel


def build_trick():
    all_cards = range(2, 10)
    cards = random.choices(all_cards, k=3)
    return Trick(
        cards=[Card(suit="S", rank=card) for card in cards],
        first_player_index=0,
    )


def train_model_test():
    game_states = []
    for _ in range(10):
        cards = random.choices(range(2, 11), k=4)
        current_trick = Trick(
            cards=[Card(suit="S", rank=card) for card in cards[:3]],
            first_player_index=0,
        )
        game_state = GameState(
            previous_tricks=[],
            current_trick=current_trick,
            current_player_index=3,
            player_hand=[],
            played_card=Card(suit="S", rank=cards[3]),
        )
        game_states.append(game_state)

    model = HeartsTransformerModel()
    model.build()
    model.model.summary()

    model.train(game_states, epochs=50, batch_size=16)

    model.save_weights("models/test_hearts.weights.h5")


def predict_model_test():
    model = HeartsTransformerModel()
    model.build()
    model.load_weights("models/test_hearts.weights.h5")
    model.model.summary()

    cards = random.choices(range(2, 11), k=4)
    current_trick = Trick(
        cards=[Card(suit="S", rank=card) for card in cards[:3]],
        first_player_index=0,
    )
    game_state = GameState(
        previous_tricks=[],
        current_trick=current_trick,
        current_player_index=3,
        player_hand=[],
    )

    predictions = model.predict(game_state)
    predicted_card_idx = np.argmax(predictions[0])
    predicted_card = decode_card(predicted_card_idx)

    print(f"Predicted card: {predicted_card.suit}{predicted_card.rank}")

    # Get the top 10 most probable cards
    probs = predictions[0]
    top_indices = np.argsort(probs)[-52:][
        ::-1
    ]  # Get indices of top 10 cards in descending order

    print("\nTop most probable cards:")
    for i, idx in enumerate(top_indices):
        card = decode_card(idx)
        if card.suit == "S":
            print(f"{card.suit}{card.rank} - {probs[idx] * 100:.2f}%")


if __name__ == "__main__":
    train_model_test()

    predict_model_test()
