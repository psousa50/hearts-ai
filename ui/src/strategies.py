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
        return min(valid_moves, key=lambda card: 
            card.rank + 13 if (card.suit == 'H' or (card.suit == 'S' and card.rank == 12))
            else card.rank)

class AggressiveStrategy(Strategy):
    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        # Play highest value card, preferring hearts and queen of spades
        return max(valid_moves, key=lambda card: 
            card.rank + 13 if (card.suit == 'H' or (card.suit == 'S' and card.rank == 12))
            else card.rank)

class AIStrategy(Strategy):
    def __init__(self, endpoint: str = "http://localhost:8000/predict"):
        self.endpoint = endpoint
        self.fallback = AvoidPointsStrategy()
        self.game_id = 0
        self.trick_number = 0
        self.previous_tricks = []
        self.current_trick_cards = []

    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        try:
            # Convert cards to the format expected by the service
            state = {
                "game_id": self.game_id,
                "trick_number": self.trick_number,
                "previous_tricks": self.previous_tricks,
                "current_trick_cards": self.current_trick_cards,  # Now using tracked cards
                "current_player_index": 3,  # AI is always player 3
                "hand": [(c.suit, c.rank) for c in hand],
                "valid_moves": [(c.suit, c.rank) for c in valid_moves]
            }
            
            # Make request to AI service with longer timeout
            response = requests.post(
                self.endpoint, 
                json=state, 
                timeout=5.0,  # Increased timeout
                headers={"Content-Type": "application/json"}
            )
            prediction = response.json()
            
            # Find the predicted card in valid_moves
            for card in valid_moves:
                if card.suit == prediction["suit"] and card.rank == prediction["rank"]:
                    return card

            return valid_moves[0]

        except Exception as e:
            print(f"AI service unavailable, using fallback strategy: {e}")
            raise
        
        # Fallback to AvoidPoints strategy
        return self.fallback.choose_card(hand, valid_moves)

    def update_game_state(self, trick_completed: bool, winner: Optional[int] = None):
        if trick_completed:
            self.trick_number += 1
            if winner is not None:
                # Store completed trick
                self.previous_tricks.append({
                    "cards": self.current_trick_cards.copy(),  # Save current trick cards
                    "winner": winner
                })
            # Clear current trick cards
            self.current_trick_cards = []

