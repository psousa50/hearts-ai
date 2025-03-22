import random
from typing import List

from hearts_game_core.game import CompletedGame, Player, PlayerInfo
from hearts_game_core.game_models import Card, CompletedTrick, Trick
from strategies.strategies import StrategyGameState


class HeartsGame:
    def __init__(self, players: List[Player]):
        self.players = players
        self.reset_game()

    def reset_game(self):
        self.hearts_broken = False
        self.previous_tricks: List[CompletedTrick] = []
        self.current_trick = Trick()
        self.scores = [0] * 4
        self.hands = self.deal_cards()
        self.current_player_index = self.find_starting_player()

        self.current_trick.reset()
        self.current_trick.first_player_index = self.current_player_index

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def deal_cards(self) -> List[List[Card]]:
        # Create a deck of cards
        deck = []
        for suit in ["C", "D", "H", "S"]:
            for rank in range(2, 15):  # 2-14 (Ace is 14)
                deck.append(Card(suit=suit, rank=rank))

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
        if not self.previous_tricks and self.current_trick.is_empty:
            return [c for c in hand if c.suit == "C" and c.rank == 2]

        # If a suit was led, must follow suit if possible
        if not self.current_trick.is_empty:
            lead_suit = self.current_trick.lead_suit
            same_suit = [c for c in hand if c.suit == lead_suit]
            if same_suit:
                return same_suit
            # If can't follow suit, can play any card including hearts
            return hand.copy()

        # Leading a trick (current_trick is empty)
        # On first trick, can't play hearts or queen of spades
        if not self.previous_tricks:
            safe_cards = [
                c for c in hand if not (c.suit == "H" or c == Card.QueenOfSpades)
            ]
            if safe_cards:
                return safe_cards

        # If hearts not broken, avoid hearts if possible
        if not self.hearts_broken:
            non_hearts = [c for c in hand if c.suit != "H"]
            if non_hearts:
                return non_hearts

        return hand.copy()

    def choose_card(self, player_idx: int) -> Card:
        valid_moves = self.get_valid_moves(player_idx)
        strategy = self.players[player_idx].strategy
        game_state = None
        if strategy.requires_game_state:
            game_state = StrategyGameState(
                previous_tricks=self.previous_tricks,
                current_trick=self.current_trick,
                current_player_index=player_idx,
                player_hand=self.hands[player_idx],
                valid_moves=valid_moves,
            )
        card = self.players[player_idx].strategy.choose_card(valid_moves, game_state)
        return card if card in valid_moves else None

    def play_card(self, card: Card):
        player_idx = self.current_player_index
        self.hands[player_idx].remove(card)

        if card.suit == "H":
            self.hearts_broken = True

        self.current_trick.add_card(player_idx, card)

        if self.current_trick.is_completed:
            self.current_player_index = self.complete_trick()
        else:
            self.current_player_index = (player_idx + 1) % 4

    def complete_trick(self) -> int:
        lead_suit = self.current_trick.lead_suit
        trick_cards = self.current_trick.cards
        winner_index = trick_cards.index(
            max(
                trick_cards, key=lambda card: card.rank if card.suit == lead_suit else 0
            )
        )

        score = self.current_trick.score()
        self.scores[winner_index] += score

        self.previous_tricks.append(
            CompletedTrick(
                cards=self.current_trick.cards,
                first_player_index=self.current_trick.first_player_index,
                winner_index=winner_index,
                score=score,
            )
        )

        self.current_trick.reset()
        self.current_trick.first_player_index = winner_index

        return winner_index

    def is_game_over(self):
        return all(len(hand) == 0 for hand in self.hands)

    def play_game(self) -> CompletedGame:
        while not self.is_game_over():
            card_to_play = self.choose_card(self.current_player_index)
            self.play_card(card_to_play)

        winner_index = min(enumerate(self.scores), key=lambda x: x[1])[0]
        return CompletedGame(
            players=[
                PlayerInfo(
                    name=player.name,
                    strategy=player.strategy.__class__.__name__,
                    score=score,
                )
                for player, score in zip(self.players, self.scores)
            ],
            winner_index=winner_index,
            completed_tricks=self.previous_tricks,
        )
