from typing import List

from hearts_game_core.game_models import Card, CompletedTrick, Trick, CompletedGame, GameCurrentState, PlayerInfo
from hearts_game_core.strategies import StrategyGameState, Player
from hearts_game_core.deck import Deck


class HeartsGame:
    def __init__(self, players: List[Player], deck: Deck = None):
        self.players = players
        self.deck = deck or Deck()
        self.reset_game()

    def reset_game(self):
        for player, hand in zip(self.players, self.deal_cards()):
            player.initial_hand = hand if len(player.initial_hand) == 0 else player.initial_hand
            player.hand = player.initial_hand.copy()
            player.score = 0
        self.current_state = GameCurrentState()
        self.current_state.set_first_player(self.find_starting_player())

    @property
    def current_player_index(self) -> int:
        return self.current_state.current_player_index

    @property
    def current_trick(self) -> Trick:
        return self.current_state.current_trick

    @property
    def previous_tricks(self) -> List[CompletedTrick]:
        return self.current_state.previous_tricks

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def deal_cards(self) -> List[List[Card]]:
        hands = self.deck.deal(4, 13)
        return [sorted(hand, key=lambda c: (c.suit, c.rank)) for hand in hands]

    def find_starting_player(self) -> int:
        for i, player in enumerate(self.players):
            for card in player.hand:
                if card == Card.TwoOfClubs:
                    return i
        return 0

    def get_valid_moves(self, player_idx: int) -> List[Card]:
        player = self.players[player_idx]
        hand = player.hand

        # First card of first trick must be 2 of clubs
        if not self.previous_tricks and self.current_trick.is_empty:
            return [c for c in hand if c == Card.TwoOfClubs]

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
        if not self.current_state.hearts_broken:
            non_hearts = [c for c in hand if c.suit != "H"]
            if non_hearts:
                return non_hearts

        return hand.copy()

    def choose_card(self, player_idx: int) -> Card:
        valid_moves = self.get_valid_moves(player_idx)
        strategy_game_state = StrategyGameState(
            game_state=self.current_state,
            player_hand=self.players[player_idx].hand,
            player_index=player_idx,
            player_score=self.players[player_idx].score,
            valid_moves=valid_moves,
        )
        card = self.players[player_idx].strategy.choose_card(strategy_game_state)
        return card if card in valid_moves else None

    def play_card(self, card: Card):
        player_idx = self.current_player_index
        self.players[player_idx].hand.remove(card)

        if card.suit == "H":
            self.current_state.hearts_broken = True

        self.current_trick.add_card(player_idx, card)

        if self.current_trick.is_completed:
            current_player = self.complete_trick()
            self.set_current_player(current_player)
        else:
            self.set_current_player((player_idx + 1) % 4)
    
    def set_current_player(self, player_idx: int):
        self.current_state.current_player_index = player_idx

    def complete_trick(self) -> int:
        lead_suit = self.current_trick.lead_suit
        trick_cards = self.current_trick.cards
        winner_index = trick_cards.index(
            max(
                trick_cards, key=lambda card: card.rank if card.suit == lead_suit else 0
            )
        )

        score = self.current_trick.score()
        self.players[winner_index].score += score

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
        return all(len(player.hand) == 0 for player in self.players)

    def play_next_card(self):
        card_to_play = self.choose_card(self.current_player_index)
        self.play_card(card_to_play)

    def play_game(self) -> CompletedGame:
        while not self.is_game_over():
            self.play_next_card()
        winner_index = min(enumerate(self.players), key=lambda x: x[1].score)[0]

        return CompletedGame(
            players=[
                PlayerInfo(
                    name=self.players[player_index].name,
                    strategy=self.players[player_index].strategy.__class__.__name__,
                    initial_hand=self.players[player_index].initial_hand,
                    score=self.players[player_index].score,
                )
                for player_index in range(4)
            ],
            winner_index=winner_index,
            completed_tricks=self.previous_tricks,
        )
