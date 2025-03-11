import os
import random

import numpy as np
from predict_request import Card, GameState, Trick
from transformer_encoding import SUITS, build_input_sequence
from transformer_model import build_model, train_model


def build_trick():
    all_cards = range(2, 10)
    cards = random.choices(all_cards, k=3)
    return Trick(
        cards=[Card(suit="S", rank=card) for card in cards],
        first_player_index=0,
    )


def train_model_test():
    game_states = []
    for _ in range(1000):
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

    model = build_model()
    model.summary()

    train_model(model, game_states, epochs=50, batch_size=16)

    model.save_weights("models/hearts.weights.h5")


def predict_model_test():
    model = build_model()
    model.load_weights("models/hearts.weights.h5")
    model.summary()

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

    input_sequence = build_input_sequence(game_state)
    input_sequence = np.expand_dims(input_sequence, axis=0)

    predictions = model.predict(input_sequence)
    predicted_card_idx = np.argmax(predictions[0])

    suit_idx = predicted_card_idx // 13
    rank = (predicted_card_idx % 13) + 2
    predicted_card = Card(suit=SUITS[suit_idx], rank=rank)

    print(f"Predicted card: {predicted_card.suit}{predicted_card.rank}")

    # Get the top 10 most probable cards
    probs = predictions[0]
    top_indices = np.argsort(probs)[-52:][
        ::-1
    ]  # Get indices of top 10 cards in descending order

    print("\nTop most probable cards:")
    for i, idx in enumerate(top_indices):
        suit_idx = idx // 13
        rank = (idx % 13) + 2
        card = Card(suit=SUITS[suit_idx], rank=rank)
        if card.suit == "S":
            print(f"{card.suit}{card.rank} - {probs[idx] * 100:.2f}%")


if __name__ == "__main__":
    # train_model_test()

    predict_model_test()
