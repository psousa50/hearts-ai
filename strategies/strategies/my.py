import sys
from typing import List

from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState

DEBUG = False


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force output to be displayed immediately


class MyStrategy(Strategy):

    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        game_state = strategy_game_state.game_state
        debug_print("------------------------------------------------")
        debug_print(
            "Player hand:", [str(card) for card in strategy_game_state.player_hand]
        )
        debug_print("Current trick:", game_state.current_trick)
        card = self._choose_card(strategy_game_state)

        debug_print("Chosen card:", card)

        if card not in strategy_game_state.valid_moves:
            debug_print("Valid moves:", strategy_game_state.valid_moves)
            return strategy_game_state.valid_moves[0]
        return card

    def _choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        game_state = strategy_game_state.game_state
        if game_state.current_trick.is_empty and not game_state.previous_tricks:
            return Card(suit="C", rank=2)
        numberOfCardsOutPerSuit = {
            "C": 0,
            "D": 0,
            "H": 0,
            "S": 0,
        }
        for card in strategy_game_state.player_hand:
            numberOfCardsOutPerSuit[card.suit] += 1
        for previous_trick in game_state.previous_tricks:
            for card in previous_trick.cards:
                numberOfCardsOutPerSuit[card.suit] += 1
        for card in game_state.current_trick.all_cards():
            numberOfCardsOutPerSuit[card.suit] += 1

        debug_print("Number of cards out per suit:", numberOfCardsOutPerSuit)
        excludedSuits = ["H"]
        queenOfSpadesIsOut = False
        for previous_trick in game_state.previous_tricks:
            for card in previous_trick.cards:
                if card == Card.QueenOfSpades:
                    queenOfSpadesIsOut = True
                    break
        if not queenOfSpadesIsOut:
            excludedSuits.append("S")
        debug_print("Queen of spades is out:", queenOfSpadesIsOut)
        debug_print("Excluded suits:", excludedSuits)

        if game_state.current_trick.is_empty:
            suitWithLessCardsOutButNotZero = min(
                numberOfCardsOutPerSuit.items(),
                key=lambda item: (
                    item[1]
                    if item[1] > 0 and item[0] not in excludedSuits
                    else float("inf")
                ),
            )

            debug_print(
                "Suit with less cards but not zero:", suitWithLessCardsOutButNotZero
            )
            sortedHand = self.sorted_hand_from_suit(
                strategy_game_state, suitWithLessCardsOutButNotZero[0]
            )
            debug_print("Sorted hand:", sortedHand)
            if numberOfCardsOutPerSuit[suitWithLessCardsOutButNotZero[0]] > 7:
                if sortedHand:
                    debug_print("Playing lowest card in sorted hand")
                    return sortedHand[0]
                else:
                    debug_print("Playing lowest card in hand")
                    return strategy_game_state.player_hand[0]
            else:
                if sortedHand:
                    debug_print("Playing highest card in sorted hand")
                    return sortedHand[-1]
                else:
                    debug_print("Playing highest card in hand")
                    return strategy_game_state.player_hand[-1]
        else:
            lead_suit = game_state.current_trick.lead_suit
            debug_print("Lead suit:", lead_suit)
            trick_cards_in_suit = [
                card
                for card in game_state.current_trick.all_cards()
                if card.suit == lead_suit
            ]
            debug_print("Trick cards in lead suit:", trick_cards_in_suit)

            highestCardInTrick = max(trick_cards_in_suit, key=lambda card: card.rank)
            debug_print("Highest card in trick:", highestCardInTrick)

            canFollowSuit = lead_suit in [
                card.suit for card in strategy_game_state.player_hand
            ]
            debug_print("Can follow suit:", canFollowSuit)
            if canFollowSuit:
                sortedHand = self.sorted_hand_from_suit(strategy_game_state, lead_suit)
                debug_print("Sorted hand:", sortedHand)
                score = game_state.current_trick.score()
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
                hasQueenOfSpades = Card.QueenOfSpades in strategy_game_state.player_hand
                debug_print("Has queen of spades:", hasQueenOfSpades)
                if hasQueenOfSpades:
                    return Card.QueenOfSpades
                sortedHearts = self.sorted_hand_from_suit(strategy_game_state, "H")
                debug_print("Sorted hearts:", sortedHearts)
                if sortedHearts:
                    return sortedHearts[-1]
                else:
                    return strategy_game_state.valid_moves[0]

    def sorted_hand_from_suit(
        self, strategy_game_state: StrategyGameState, suit: str
    ) -> List[Card]:
        return sorted(
            [card for card in strategy_game_state.player_hand if card.suit == suit],
            key=lambda card: card.rank,
        )
