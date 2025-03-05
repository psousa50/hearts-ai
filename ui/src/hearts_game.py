import random
from typing import List, Optional, Tuple

from card import Card
from strategies import AIStrategy, Strategy


class Player:
    def __init__(self, name: str, strategy: Strategy):
        self.name = name
        self.strategy = strategy


class HeartsGame:
    def __init__(self, players: List[Player]):
        self.players = players
        self.reset_game()

    def reset_game(self):
        self.hearts_broken = False
        self.tricks = []
        self.current_trick = []
        self.scores = [0] * 4
        self.hands = self.deal_cards()
        self.current_player_index = self.find_starting_player()

    def deal_cards(self) -> List[List[Card]]:
        # Create a deck of cards
        deck = []
        for suit in ["C", "D", "H", "S"]:
            for rank in range(2, 15):  # 2-14 (Ace is 14)
                deck.append(Card(suit, rank))

        # Shuffle and deal
        random.shuffle(deck)
        hands = [[] for _ in range(4)]
        for i, card in enumerate(deck):
            hands[i % 4].append(card)

        # Sort hands
        for hand in hands:
            hand.sort(key=lambda c: (c.suit, c.rank))

        return hands

    def find_starting_player(self) -> int:
        # Player with 2 of clubs starts
        for i, hand in enumerate(self.hands):
            for card in hand:
                if card.suit == "C" and card.rank == 2:
                    return i
        return 0

    def get_valid_moves(self, player_idx: int) -> List[Card]:
        hand = self.hands[player_idx]

        # First card of first trick must be 2 of clubs
        if not self.tricks and not self.current_trick:
            return [c for c in hand if c.suit == "C" and c.rank == 2]

        # If a suit was led, must follow suit if possible
        if self.current_trick:
            lead_suit = self.current_trick[0][0].suit
            same_suit = [c for c in hand if c.suit == lead_suit]
            if same_suit:
                return same_suit

        # On first trick, can't play hearts or queen of spades
        if not self.tricks:
            safe_cards = [
                c
                for c in hand
                if not (c.suit == "H" or (c.suit == "S" and c.rank == 12))
            ]
            if safe_cards:
                return safe_cards

        # If hearts not broken, avoid hearts if possible
        if not self.hearts_broken:
            non_hearts = [c for c in hand if c.suit != "H"]
            if non_hearts:
                return non_hearts

        return hand.copy()

    def play_card(self, player_idx: int, card: Optional[Card] = None) -> Card:
        valid_moves = self.get_valid_moves(player_idx)

        if card is None:
            # Let the strategy choose a card
            card = self.players[player_idx].strategy.choose_card(
                self.hands[player_idx], valid_moves
            )
        else:
            # Validate the chosen card
            if card not in valid_moves:
                return None, None

        if card is None:
            return None, None

        # Remove the card from hand
        card_idx = self.hands[player_idx].index(card)
        self.hands[player_idx].remove(card)

        # Update game state
        if card.suit == "H":
            self.hearts_broken = True

        # Add to current trick
        self.current_trick.append((card, player_idx))

        # Update AI game state
        for player in self.players:
            if isinstance(player.strategy, AIStrategy):
                player.strategy.current_trick_cards.append((card.suit, card.rank))

        # Move to next player
        self.current_player = (player_idx + 1) % 4

        return card, card_idx

    def complete_trick(self):
        """Complete the current trick and determine the winner."""
        if len(self.current_trick) != 4:
            raise ValueError("Cannot complete trick: not enough cards played")

        # Determine winning card
        lead_suit = self.current_trick[0][0].suit
        # First check if any cards followed suit
        followed_suit_cards = [
            (card, player)
            for card, player in self.current_trick
            if card.suit == lead_suit
        ]
        # If no one followed suit, consider all cards
        cards_to_compare = (
            followed_suit_cards if followed_suit_cards else self.current_trick
        )
        winning_card, winner_idx = max(cards_to_compare, key=lambda x: x[0].rank)

        # Calculate points
        points = sum(1 for card, _ in self.current_trick if card.suit == "H")
        if any(card.suit == "S" and card.rank == 12 for card, _ in self.current_trick):
            points += 13

        # Update scores
        self.scores[winner_idx] += points

        # Save completed trick
        self.tricks.append(
            {
                "cards": [
                    {
                        "card": {"suit": card.suit, "rank": card.rank},
                        "player_index": player_idx,
                    }
                    for card, player_idx in self.current_trick
                ],
                "winner": winner_idx,
                "points": points,
            }
        )

        # Reset for next trick
        self.current_trick = []
        self.current_player_index = winner_idx  # Next trick starts with the winner

        # Update trick number and state for AI strategies
        for player in self.players:
            if isinstance(player.strategy, AIStrategy):
                player.strategy.trick_number += 1
                player.strategy.previous_tricks.append(self.tricks[-1])
                player.strategy.current_trick_cards = []  # Clear current trick cards
                player.strategy.current_trick_cards_raw = []  # Clear raw trick cards

        # Check if game is over
        if not any(hand for hand in self.hands):
            self.game_over = True

        return True  # Return True to indicate trick was completed successfully

    def game_over(self):
        return all(len(hand) == 0 for hand in self.hands)
