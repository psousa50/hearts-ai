import json
import random
import sys
from typing import List, Optional

import requests
from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState
from request_models.models import GameState, PredictRequest

DEBUG = False


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force output to be displayed immediately


class HumanStrategy(Strategy):
    def choose_card(self, _gameState: Optional[StrategyGameState]) -> Card:
        raise NotImplementedError


class RandomStrategy(Strategy):
    """Strategy that plays random valid moves"""

    def choose_card(
        self, valid_moves: List[Card], _gameState: Optional[StrategyGameState]
    ) -> Card:
        """Choose a random valid card to play"""
        if not valid_moves:
            return _gameState.player_hand[0]
        return random.choice(valid_moves)


class AvoidPointsStrategy(Strategy):
    def choose_card(
        self, valid_moves: List[Card], _gameState: Optional[StrategyGameState]
    ) -> Card:
        # Play lowest value card, avoiding hearts and queen of spades
        return min(
            valid_moves,
            key=lambda card: card.rank + 13
            if (card.suit == "H" or card == Card.QueenOfSpades)
            else card.rank,
        )


class AggressiveStrategy(Strategy):
    def choose_card(
        self, valid_moves: List[Card], _gameState: Optional[StrategyGameState]
    ) -> Card:
        # Play highest value card, preferring hearts and queen of spades
        return max(
            valid_moves,
            key=lambda card: card.rank + 13
            if (card.suit == "H" or card == Card.QueenOfSpades)
            else card.rank,
        )


class AIStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.endpoint = "http://localhost:8000/predict"

    def choose_card(
        self, valid_moves: List[Card], game_state: Optional[StrategyGameState]
    ) -> Card:
        """Choose a card to play using the AI model"""
        if not game_state:
            return valid_moves[0]
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
            json_data = predict_request.json()
            debug_print("Sending prediction request:", json.dumps(json_data, indent=2))

            # Send request to AI service
            response = requests.post(self.endpoint, json=json_data, timeout=5)
            response.raise_for_status()
            result = response.json()

            # debug_print("Received response from AI service:", json.dumps(result, indent=2))

            # Convert predicted move to Card
            if isinstance(result, dict) and "suit" in result and "rank" in result:
                predicted_card = Card(suit=result["suit"], rank=result["rank"])
                # Verify the predicted card is in valid_moves
                if predicted_card in game_state.valid_moves:
                    return predicted_card
                debug_print(f"AI predicted invalid move: {predicted_card}")
                raise ValueError("AI predicted invalid move")

            debug_print(f"Invalid prediction format: {result}")
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


class MyStrategy(Strategy):
    def requires_game_state(self) -> bool:
        return True

    def choose_card(
        self, valid_moves: List[Card], _gameState: Optional[StrategyGameState]
    ) -> Card:
        if not _gameState:
            raise ValueError("Game state is required for MyStrategy")
        gameState = _gameState
        debug_print("------------------------------------------------")
        debug_print("Player hand:", [str(card) for card in gameState.player_hand])
        debug_print("Current trick:", gameState.current_trick)
        card = self._choose_card(valid_moves, gameState)

        debug_print("Chosen card:", card)

        if card not in valid_moves:
            debug_print("Valid moves:", valid_moves)
            return valid_moves[0]
        return card

    def _choose_card(
        self, valid_moves: List[Card], gameState: StrategyGameState
    ) -> Card:
        if gameState.current_trick.is_empty and not gameState.previous_tricks:
            return Card(suit="C", rank=2)
        numberOfCardsOutPerSuit = {
            "C": 0,
            "D": 0,
            "H": 0,
            "S": 0,
        }
        for card in gameState.player_hand:
            numberOfCardsOutPerSuit[card.suit] += 1
        for previous_trick in gameState.previous_tricks:
            for card in previous_trick.cards:
                numberOfCardsOutPerSuit[card.suit] += 1
        for card in gameState.current_trick.all_cards():
            numberOfCardsOutPerSuit[card.suit] += 1

        debug_print("Number of cards out per suit:", numberOfCardsOutPerSuit)
        excludedSuits = ["H"]
        queenOfSpadesIsOut = False
        for previous_trick in gameState.previous_tricks:
            for card in previous_trick.cards:
                if card == Card.QueenOfSpades:
                    queenOfSpadesIsOut = True
                    break
        if not queenOfSpadesIsOut:
            excludedSuits.append("S")
        debug_print("Queen of spades is out:", queenOfSpadesIsOut)
        debug_print("Excluded suits:", excludedSuits)

        if gameState.current_trick.is_empty:
            suitWithLessCardsOutButNotZero = min(
                numberOfCardsOutPerSuit.items(),
                key=lambda item: item[1]
                if item[1] > 0 and item[0] not in excludedSuits
                else float("inf"),
            )

            debug_print(
                "Suit with less cards but not zero:", suitWithLessCardsOutButNotZero
            )
            sortedHand = self.sorted_hand_from_suit(
                gameState, suitWithLessCardsOutButNotZero[0]
            )
            debug_print("Sorted hand:", sortedHand)
            if numberOfCardsOutPerSuit[suitWithLessCardsOutButNotZero[0]] > 7:
                if sortedHand:
                    debug_print("Playing lowest card in sorted hand")
                    return sortedHand[0]
                else:
                    debug_print("Playing lowest card in hand")
                    return gameState.player_hand[0]
            else:
                if sortedHand:
                    debug_print("Playing highest card in sorted hand")
                    return sortedHand[-1]
                else:
                    debug_print("Playing highest card in hand")
                    return gameState.player_hand[-1]
        else:
            lead_suit = gameState.current_trick.lead_suit
            debug_print("Lead suit:", lead_suit)
            trick_cards_in_suit = [
                card
                for card in gameState.current_trick.all_cards()
                if card.suit == lead_suit
            ]
            debug_print("Trick cards in lead suit:", trick_cards_in_suit)

            highestCardInTrick = max(trick_cards_in_suit, key=lambda card: card.rank)
            debug_print("Highest card in trick:", highestCardInTrick)

            canFollowSuit = lead_suit in [card.suit for card in gameState.player_hand]
            debug_print("Can follow suit:", canFollowSuit)
            if canFollowSuit:
                sortedHand = self.sorted_hand_from_suit(gameState, lead_suit)
                debug_print("Sorted hand:", sortedHand)
                score = gameState.current_trick.score()
                debug_print("Score:", score)
                shouldTakeTrick = score == 0 and numberOfCardsOutPerSuit[lead_suit] < 7
                shouldTakeTrick = shouldTakeTrick and lead_suit not in excludedSuits
                debug_print("Should take trick:", shouldTakeTrick)
                if shouldTakeTrick:
                    return sortedHand[-1]
                else:
                    sortedHandLowerThanHighestCardInTrick = [
                        card
                        for card in sortedHand
                        if card.rank < highestCardInTrick.rank
                    ]
                    debug_print(
                        "Sorted hand lower than highest card in trick:",
                        sortedHandLowerThanHighestCardInTrick,
                    )
                    if sortedHandLowerThanHighestCardInTrick:
                        debug_print("Playing lowest card in hand")
                        return sortedHandLowerThanHighestCardInTrick[-1]
                    else:
                        debug_print("Playing highest card in hand")
                        return sortedHand[-1]
            else:
                hasQueenOfSpades = Card.QueenOfSpades in gameState.player_hand
                debug_print("Has queen of spades:", hasQueenOfSpades)
                if hasQueenOfSpades:
                    return Card.QueenOfSpades
                sortedHearts = self.sorted_hand_from_suit(gameState, "H")
                debug_print("Sorted hearts:", sortedHearts)
                if sortedHearts:
                    return sortedHearts[-1]
                else:
                    return gameState.valid_moves[0]

    def sorted_hand_from_suit(
        self, gameState: StrategyGameState, suit: str
    ) -> List[Card]:
        return sorted(
            [card for card in gameState.player_hand if card.suit == suit],
            key=lambda card: card.rank,
        )
