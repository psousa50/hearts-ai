from typing import List, Optional

import requests
from card import Card


class Strategy:
    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        raise NotImplementedError


class RandomStrategy(Strategy):
    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        return random.choice(valid_moves)


class AvoidPointsStrategy(Strategy):
    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        # Play lowest value card, avoiding hearts and queen of spades
        return min(
            valid_moves,
            key=lambda card: card.rank + 13
            if (card.suit == "H" or (card.suit == "S" and card.rank == 12))
            else card.rank,
        )


class AggressiveStrategy(Strategy):
    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        # Play highest value card, preferring hearts and queen of spades
        return max(
            valid_moves,
            key=lambda card: card.rank + 13
            if (card.suit == "H" or (card.suit == "S" and card.rank == 12))
            else card.rank,
        )


class AIStrategy(Strategy):
    def __init__(self, endpoint: str = "http://localhost:8000/predict"):
        self.endpoint = endpoint
        self.fallback = AvoidPointsStrategy()
        # Track game state
        self.trick_number = 0
        self.previous_tricks = []
        self.current_trick_cards = []

    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        try:
            # Prepare state for AI prediction
            state = {
                "state": {
                    "game_id": 0,  # Not relevant for prediction
                    "trick_number": self.trick_number,
                    "previous_tricks": self.previous_tricks,
                    "current_trick_cards": self.current_trick_cards,
                    "current_player_index": 3,  # AI is always player 3
                    "player_hand": [{"suit": c.suit, "rank": c.rank} for c in hand],
                    "played_card": None
                },
                "valid_moves": [{"suit": c.suit, "rank": c.rank} for c in valid_moves]
            }

            # Make request to AI service with longer timeout
            response = requests.post(
                self.endpoint,
                json=state,
                timeout=5.0,  # Increased timeout
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code != 200:
                print(f"AI service error: {response.text}")
                raise Exception("AI service error")
                
            prediction = response.json()
            if not isinstance(prediction, dict) or "suit" not in prediction or "rank" not in prediction:
                print(f"Invalid prediction format: {prediction}")
                raise Exception("Invalid prediction format")

            # Find the predicted card in valid_moves
            for card in valid_moves:
                if card.suit == prediction["suit"] and card.rank == prediction["rank"]:
                    return card

            print(f"Predicted card {prediction} not in valid moves: {valid_moves}")
            raise Exception("Predicted card not in valid moves")

        except Exception as e:
            print(f"AI service unavailable, using fallback strategy: {e}")
            return self.fallback.choose_card(hand, valid_moves)

    def on_trick_complete(self, winner: Optional[int] = None):
        self.trick_number += 1
        if winner is not None:
            # Store completed trick
            self.previous_tricks.append(
                {
                    "cards": self.current_trick_cards.copy(),  # Save current trick cards
                    "winner": winner,
                }
            )
        # Clear current trick cards
        self.current_trick_cards = []

    def update_game_state(self, trick_completed: bool, winner: Optional[int] = None):
        if trick_completed:
            self.on_trick_complete(winner)
