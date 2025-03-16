import json
import random
from dataclasses import asdict, dataclass
from typing import List

import requests
from card import Card, CompletedTrick, Trick
from predict_request import GameState, PredictRequest


@dataclass
class StrategyGameState:
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    valid_moves: List[Card]


class Strategy:
    def choose_card(self, gameState: StrategyGameState) -> Card:
        raise NotImplementedError


class HumanStrategy(Strategy):
    def choose_card(self, gameState: StrategyGameState) -> Card:
        raise NotImplementedError


class RandomStrategy(Strategy):
    """Strategy that plays random valid moves"""

    def choose_card(self, gameState: StrategyGameState) -> Card:
        """Choose a random valid card to play"""
        if not gameState.valid_moves:
            return gameState.player_hand[0]
        return random.choice(gameState.valid_moves)


class AvoidPointsStrategy(Strategy):
    def choose_card(self, gameState: StrategyGameState) -> Card:
        # Play lowest value card, avoiding hearts and queen of spades
        return min(
            gameState.valid_moves,
            key=lambda card: card.rank + 13
            if (card.suit == "H" or card == Card.QueenOfSpades)
            else card.rank,
        )


class AggressiveStrategy(Strategy):
    def choose_card(self, gameState: StrategyGameState) -> Card:
        # Play highest value card, preferring hearts and queen of spades
        return max(
            gameState.valid_moves,
            key=lambda card: card.rank + 13
            if (card.suit == "H" or card == Card.QueenOfSpades)
            else card.rank,
        )


class AIStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.endpoint = "http://localhost:8000/predict"

    def choose_card(self, game_state: StrategyGameState) -> Card:
        """Choose a card to play using the AI model"""
        try:
            state = GameState(
                previous_tricks=game_state.previous_tricks,
                current_trick=game_state.current_trick,
                current_player_index=game_state.current_player_index,
                player_hand=game_state.player_hand,
            )

            # Create prediction request
            predict_request = PredictRequest(
                state=state, valid_moves=game_state.valid_moves
            )
            json_data = asdict(predict_request)
            # print("Sending prediction request:", json.dumps(json_data, indent=2))

            # Send request to AI service
            response = requests.post(self.endpoint, json=json_data, timeout=5)
            response.raise_for_status()
            result = response.json()

            # print("Received response from AI service:", json.dumps(result, indent=2))

            # Convert predicted move to Card
            if isinstance(result, dict) and "suit" in result and "rank" in result:
                predicted_card = Card(suit=result["suit"], rank=result["rank"])
                # Verify the predicted card is in valid_moves
                if predicted_card in game_state.valid_moves:
                    return predicted_card
                print(f"AI predicted invalid move: {predicted_card}")
                raise ValueError("AI predicted invalid move")

            print(f"Invalid prediction format: {result}")
            raise ValueError("Invalid prediction format")

        except Exception as e:
            raise ValueError(f"AI service error: {str(e)}")


class ReplayStrategy(Strategy):
    def __init__(self, cards: List[Card]):
        self.cards = cards.copy()  # Make a copy to avoid modifying the original
        self.current_index = 0

    def choose_card(self, game_state: StrategyGameState) -> Card:
        if self.current_index >= len(self.cards):
            raise ValueError("Replay strategy ran out of cards")

        card = self.cards[self.current_index]
        self.current_index += 1

        # Verify the card is valid
        if card not in game_state.valid_moves:
            raise ValueError("Replay strategy predicted invalid move")

        return card

    def reset(self):
        """Reset the replay sequence back to the start"""
        self.current_index = 0
