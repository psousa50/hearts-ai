import json
import random
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import requests
from card import Card, CompletedTrick


@dataclass
class CardJson:
    suit: str
    rank: int

    @classmethod
    def from_card(cls, card: Card) -> 'CardJson':
        return cls(suit=card.suit, rank=card.rank)

    def to_card(self) -> Card:
        return Card(suit=self.suit, rank=self.rank)

    def to_dict(self) -> Dict[str, Any]:
        return {"suit": self.suit, "rank": self.rank}

@dataclass
class TrickCardJson:
    card: CardJson
    player_index: int

    @classmethod
    def from_raw_card(cls, suit: str, rank: int, player_index: int) -> 'TrickCardJson':
        return cls(card=CardJson(suit=suit, rank=rank), player_index=player_index)

    def to_dict(self) -> Dict[str, Any]:
        return {"card": self.card.to_dict(), "player_index": self.player_index}

@dataclass
class CompletedTrickJson:
    cards: List[TrickCardJson]
    winner: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cards": [card.to_dict() for card in self.cards],
            "winner": self.winner
        }

@dataclass
class PredictionStateJson:
    game_id: int
    trick_number: int
    previous_tricks: List[CompletedTrickJson]
    current_trick_cards: List[TrickCardJson]
    current_player_index: int
    player_hand: List[CardJson]
    played_card: Optional[CardJson] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "trick_number": self.trick_number,
            "previous_tricks": [trick.to_dict() for trick in self.previous_tricks],
            "current_trick_cards": [card.to_dict() for card in self.current_trick_cards],
            "current_player_index": self.current_player_index,
            "player_hand": [card.to_dict() for card in self.player_hand],
            "played_card": self.played_card.to_dict() if self.played_card else None
        }

@dataclass
class PredictionRequest:
    state: PredictionStateJson
    valid_moves: List[CardJson]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.to_dict(),
            "valid_moves": [move.to_dict() for move in self.valid_moves]
        }

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
        self.fallback = RandomStrategy()
        self.game_id = 0
        self.trick_number = 0
        self.previous_tricks = []
        self.current_trick_cards = []  # List of (card, player_index) tuples
        self.current_trick_cards_raw = []  # List of raw (suit, rank, player_index) tuples

    def choose_card(self, gameState: StrategyGameState) -> Card:
        """Choose a card to play using the AI model"""
        try:
            # Convert current trick cards to proper format
            trick_cards = [
                TrickCardJson.from_raw_card(suit, rank, player_idx)
                for (suit, rank, player_idx) in self.current_trick_cards_raw[-4:]
            ]

            # Get only the last 3 tricks to prevent state from getting too large
            recent_tricks = [CompletedTrickJson(**trick) for trick in self.previous_tricks[-3:]] if self.previous_tricks else []

            # Create prediction state
            state = PredictionStateJson(
                game_id=self.game_id,
                trick_number=self.trick_number,
                previous_tricks=recent_tricks,
                current_trick_cards=trick_cards,
                current_player_index=3,  # AI is always player 3
                player_hand=[CardJson.from_card(c) for c in gameState.player_hand]
            )

            # Create prediction request
            request = PredictionRequest(
                state=state,
                valid_moves=[CardJson.from_card(c) for c in gameState.valid_moves]
            )

            # Prepare request data
            data = request.to_dict()

            print("Sending request to AI service:", json.dumps(data, indent=2))

            # Send request to AI service
            response = requests.post(
                "http://localhost:8000/predict", json=data, timeout=5
            )
            response.raise_for_status()
            result = response.json()

            print("Received response from AI service:", json.dumps(result, indent=2))

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
            print(f"AI service error: {str(e)}, falling back to random strategy")
            # Fall back to random strategy
            return self.fallback.choose_card(gameState)

    def update_game_state(self, trick_completed: bool, winner: Optional[int] = None):
        """Update the game state after a trick is completed"""
        if trick_completed:
            # Add the current trick to previous tricks
            self.previous_tricks.append(
                {
                    "cards": [
                        {
                            "card": {"suit": suit, "rank": rank},
                            "player_index": player_idx,
                        }
                        for (suit, rank, player_idx) in self.current_trick_cards_raw[
                            -4:
                        ]
                    ],
                    "winner": winner,
                }
            )
            self.trick_number += 1
            self.current_trick_cards = []
            self.current_trick_cards_raw = []


class ReplayStrategy(Strategy):
    def __init__(self, cards: List[Card]):
        self.cards = cards.copy()  # Make a copy to avoid modifying the original
        self.current_index = 0
        self.fallback = RandomStrategy()  # Fallback to random if we run out of cards

    def choose_card(self, hand: List[Card], valid_moves: List[Card]) -> Card:
        if self.current_index >= len(self.cards):
            print("Warning: Replay strategy ran out of cards, falling back to random")
            return self.fallback.choose_card(hand, valid_moves)

        card = self.cards[self.current_index]
        self.current_index += 1

        # Verify the card is valid
        if card not in valid_moves:
            print(
                f"Warning: Replay card {card} not in valid moves {valid_moves}, falling back to random"
            )
            return self.fallback.choose_card(hand, valid_moves)

        return card

    def reset(self):
        """Reset the replay sequence back to the start"""
        self.current_index = 0
