import json
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from card import Card, CompletedTrick, Trick


@dataclass
class GameState:
    game_id: int
    trick_number: int
    previous_tricks: List[CompletedTrick]
    current_trick: Trick
    current_player_index: int
    player_hand: List[Card]
    played_card: Optional[Card] = None

    def __post_init__(self):
        # Prepare data for JSON serialization
        self._previous_tricks_json = [
            {
                "cards": [
                    {
                        "card": {"suit": card.suit, "rank": card.rank},
                        "player_index": i,
                    }
                    for i, card in enumerate(trick.cards)
                ],
                "winner": trick.winner,
            }
            for trick in self.previous_tricks
        ]

        self._player_hand_json = [
            {"suit": card.suit, "rank": card.rank} for card in self.player_hand
        ]

        self._played_card_json = (
            {"suit": self.played_card.suit, "rank": self.played_card.rank}
            if self.played_card
            else None
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "trick_number": self.trick_number,
            "previous_tricks": self._previous_tricks_json,
            "current_trick": self.current_trick,
            "current_player_index": self.current_player_index,
            "player_hand": self._player_hand_json,
            "played_card": self._played_card_json,
        }


@dataclass
class PredictRequest:
    state: GameState
    valid_moves: List[Card]

    def to_json(self) -> str:
        """Convert the request to a JSON string"""
        return json.dumps(self.to_dict())


@dataclass
class StrategyGameState:
    tricks: List[CompletedTrick]
    current_trick: List[Card]
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
        self.game_id = 0

    def choose_card(self, gameState: StrategyGameState) -> Card:
        """Choose a card to play using the AI model"""
        try:
            # Convert current trick cards to proper format
            trick_cards = [
                TrickCard(card=card, player_index=i)
                for i, card in enumerate(gameState.current_trick.cards)
                if card is not None
            ]

            # Create prediction state
            state = GameState(
                game_id=self.game_id,
                trick_number=len(
                    gameState.tricks
                ),  # Current trick number is the number of completed tricks
                previous_tricks=gameState.tricks[-3:]
                if gameState.tricks
                else [],  # Get only the last 3 tricks
                current_trick=trick_cards,
                current_player_index=3,  # AI is always player 3
                player_hand=gameState.player_hand,
            )

            # Create prediction request
            request = PredictRequest(state=state, valid_moves=gameState.valid_moves)

            # Prepare request data and convert to JSON
            request_json = request.to_json()

            # print("Sending request to AI service:", json.dumps(request.to_dict(), indent=2))

            # Send request to AI service
            response = requests.post(
                "http://localhost:8000/predict", json=request.to_dict(), timeout=5
            )
            response.raise_for_status()
            result = response.json()

            # print("Received response from AI service:", json.dumps(result, indent=2))

            # Convert predicted move to Card
            if isinstance(result, dict) and "suit" in result and "rank" in result:
                predicted_card = Card(suit=result["suit"], rank=result["rank"])
                # Verify the predicted card is in valid_moves
                if predicted_card in gameState.valid_moves:
                    return predicted_card
                print(f"AI predicted invalid move: {predicted_card}")
                raise ValueError("AI predicted invalid move")

            print(f"Invalid prediction format: {result}")
            raise ValueError("Invalid prediction format")

        except Exception as e:
            raise ValueError(
                f"AI service error: {str(e)}, falling back to random strategy"
            )

    def update_game_id(self, game_id: int):
        """Update the game ID"""
        self.game_id = game_id


class ReplayStrategy(Strategy):
    def __init__(self, cards: List[Card]):
        self.cards = cards.copy()  # Make a copy to avoid modifying the original
        self.current_index = 0

    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        if self.current_index >= len(self.cards):
            raise ValueError("Replay strategy ran out of cards")

        card = self.cards[self.current_index]
        self.current_index += 1

        # Verify the card is valid
        if card not in valid_moves:
            raise ValueError("Replay strategy predicted invalid move")

        return card

    def reset(self):
        """Reset the replay sequence back to the start"""
        self.current_index = 0
