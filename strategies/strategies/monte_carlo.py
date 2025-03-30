import copy
import sys
from collections import defaultdict
from typing import List

import numpy as np

from hearts_game_core.deck import Deck
from hearts_game_core.game_core import HeartsGame
from hearts_game_core.game_models import Card
from hearts_game_core.random_manager import RandomManager
from hearts_game_core.strategies import Player, Strategy, StrategyGameState
from strategies.random import RandomStrategy

DEBUG = False


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force output to be displayed immediately


class MonteCarloNode:
    def __init__(self, parent=None, move=None):
        self.parent = parent
        self.move = move
        self.children = {}  # Dictionary of move -> MonteCarloNode
        self.untried_moves = []
        self.visits = 0
        self.score = 0
        self.avg_score = float("inf")  # Initialize with worst possible score
        self.best_score = float("inf")  # Track the best score seen through this node

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0

    def is_terminal(self):
        return len(self.untried_moves) == 0 and len(self.children) == 0

    def expand(self, move):
        child = MonteCarloNode(parent=self, move=move)
        self.untried_moves.remove(move)
        self.children[move] = child
        return child

    def update(self, score):
        self.visits += 1
        self.score += score
        self.avg_score = self.score / self.visits
        self.best_score = min(self.best_score, score)  # Track best (lowest) score

    def uct_select_child(self, exploration_weight=1.0) -> "MonteCarloNode":
        """Select a child node using the UCT formula."""
        # We want to minimize score in Hearts, so we use a modified UCT formula

        log_visits = np.log(self.visits) if self.visits > 0 else 0

        def uct_score(child):
            # Lower score is better in Hearts
            if child.visits == 0:
                return float("-inf")  # Prioritize unexplored nodes

            # Balance exploitation (low score) and exploration (high exploration term)
            exploitation = -child.avg_score  # Negate so higher is better
            exploration = exploration_weight * np.sqrt(log_visits / child.visits)
            return exploitation + exploration

        return max(self.children.values(), key=uct_score)


class MonteCarloStrategy(Strategy):
    def __init__(
        self,
        num_simulations: int = 5000,
        exploration_weight: float = 1.4,
        random_manager: RandomManager = None,
    ):
        self.random_manager = (
            random_manager if random_manager is not None else RandomManager()
        )
        self.num_simulations = num_simulations
        self.exploration_weight = exploration_weight
        self.move_cache = {}
        self.deck = Deck(shuffle=False, random_manager=self.random_manager)
        self.all_cards = self.deck.cards

    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        valid_moves = strategy_game_state.valid_moves
        if len(valid_moves) == 1:
            return valid_moves[0]

        debug_print(f"Valid moves: {" ".join([str(card) for card in valid_moves])}")

        # Group equivalent moves to reduce search space
        grouped_valid_moves = group_equivalent_moves(valid_moves)
        debug_print(
            f"Grouped valid moves: {" ".join([str(card) for card in grouped_valid_moves])}"
        )

        # Check cache for this game state
        # cache_key = self._get_cache_key(strategy_game_state)
        # if cache_key in self.move_cache:
        #     debug_print(f"Cache hit for {cache_key}")
        #     return self.move_cache[cache_key]

        trick_number = len(strategy_game_state.game_state.previous_tricks) + 1
        debug_print(
            f"------------------------ Trick number: {trick_number} ------------------------"
        )

        # Adjust simulation count based on game stage
        cards_left = len(strategy_game_state.player_hand)
        if cards_left <= 3:
            # Late game - we can do more exhaustive search
            num_simulations = max(10000, self.num_simulations * 3)
        elif cards_left <= 7:
            # Mid game
            num_simulations = max(7000, self.num_simulations * 2)
        else:
            num_simulations = self.num_simulations

        # Collect information about played cards
        all_played_cards = []
        for previous_trick in strategy_game_state.game_state.previous_tricks:
            for card in previous_trick.cards:
                if card is not None:
                    all_played_cards.append(card)

        for card in strategy_game_state.game_state.current_trick.cards:
            if card is not None:
                all_played_cards.append(card)

        # Calculate remaining cards in other players' hands
        all_cards_in_players_hands = [
            card
            for card in self.all_cards
            if card not in all_played_cards
            and card not in strategy_game_state.player_hand
        ]

        # Run Monte Carlo Tree Search
        best_move = self._monte_carlo_tree_search(
            strategy_game_state,
            grouped_valid_moves,
            all_cards_in_players_hands,
            num_simulations,
        )

        # Cache the result
        # self.move_cache[cache_key] = best_move

        return best_move

    def _monte_carlo_tree_search(
        self,
        strategy_game_state: StrategyGameState,
        valid_moves: List[Card],
        all_cards_in_players_hands: List[Card],
        num_simulations: int,
    ) -> Card:
        """Run the Monte Carlo Tree Search algorithm to find the best move."""
        # Create the root node
        root = MonteCarloNode()
        root.untried_moves = valid_moves.copy()

        # Run simulations
        for i in range(num_simulations):
            # Selection phase
            node = root

            # Selection: traverse the tree to find a node to expand
            while not node.is_terminal() and node.is_fully_expanded():
                node = node.uct_select_child(self.exploration_weight)

            # Expansion: if we can expand (i.e., there are untried moves), add a child
            if not node.is_terminal() and node.untried_moves:
                move = self.random_manager.choice(node.untried_moves)
                node = node.expand(move)

            # Simulation: play out the game with the selected move
            if node.move:
                try:
                    # Create a new game state for simulation
                    sim_state = copy.deepcopy(strategy_game_state)

                    # Create a game for simulation
                    game = self._create_game_for_simulation(
                        sim_state, all_cards_in_players_hands.copy()
                    )

                    # Play the selected move
                    game.play_card(node.move)

                    # Play out the game
                    completed_game = game.play_game()

                    # Get the final score
                    final_score = completed_game.players[
                        strategy_game_state.player_index
                    ].score

                    # Calculate the added score (how many points this move added)
                    added_score = final_score - strategy_game_state.player_score

                    # Backpropagation: update all nodes in the path with the result
                    while node:
                        node.update(added_score)
                        node = node.parent
                except Exception as e:
                    # If simulation fails, assign a neutral score
                    debug_print(f"Simulation error: {e}")
                    while node:
                        node.update(0)  # Neutral score
                        node = node.parent

        # Choose the best move based on average score
        best_move = None
        best_score = float("inf")

        # Print statistics for all moves
        debug_print("Move statistics:")
        for move, child in root.children.items():
            debug_print(f"{move}: avg {child.avg_score:.2f} visits: {child.visits}")
            if child.avg_score < best_score:
                best_score = child.avg_score
                best_move = move

        # If no move was found (shouldn't happen), return the first valid move
        if best_move is None and valid_moves:
            best_move = valid_moves[0]

        debug_print(f"Best move: {best_move} with added score: {best_score:.2f}")
        return best_move

    def _create_game_for_simulation(
        self,
        strategy_game_state: StrategyGameState,
        all_cards_in_players_hands: List[Card],
    ) -> HeartsGame:
        """Create a game for simulation."""
        first_player_index = (
            strategy_game_state.game_state.current_trick.first_player_index
        )
        current_player_idx = strategy_game_state.player_index

        # Create a new game with random strategies for all players
        players = [
            Player(f"Player {i}", RandomStrategy(random_manager=self.random_manager))
            for i in range(4)
        ]

        # Create a new game
        game = HeartsGame(players, random_manager=self.random_manager)

        # Set up the game state to match the current state
        # We need to access the internal attributes directly since properties don't have setters
        game._current_trick = copy.deepcopy(
            strategy_game_state.game_state.current_trick
        )
        game.completed_tricks = copy.deepcopy(
            strategy_game_state.game_state.previous_tricks
        )
        game.hearts_broken = strategy_game_state.game_state.hearts_broken

        # Set up player hands
        player_hand = strategy_game_state.player_hand.copy()

        # Shuffle the remaining cards for other players
        remaining_cards = all_cards_in_players_hands.copy()
        self.random_manager.shuffle(remaining_cards)

        # Distribute cards to players
        for i in range(4):
            if i == current_player_idx:
                game.players[i].hand = player_hand.copy()
            else:
                # Calculate how many cards this player should have
                cards_played_by_player = 0
                for trick in game.completed_tricks:
                    if trick.cards[i] is not None:
                        cards_played_by_player += 1

                if game._current_trick.cards[i] is not None:
                    cards_played_by_player += 1

                cards_to_deal = 13 - cards_played_by_player

                # Deal cards to this player
                if cards_to_deal > 0:
                    game.players[i].hand = remaining_cards[:cards_to_deal]
                    remaining_cards = remaining_cards[cards_to_deal:]
                else:
                    game.players[i].hand = []

        # Set player scores - we only know the current player's score from StrategyGameState
        # Set the current player's score
        game.players[current_player_idx].score = strategy_game_state.player_score

        # For other players, we'll set them to 0 or try to infer from previous tricks
        for i in range(4):
            if i != current_player_idx:
                # Start with 0 score
                game.players[i].score = 0

                # Try to infer scores from completed tricks
                for trick in game.completed_tricks:
                    if trick.winner_index == i:
                        # This player won this trick, add its score
                        game.players[i].score += trick.score

        return game

    def _get_cache_key(self, strategy_game_state):
        current_trick = tuple(
            (i, str(card))
            for i, card in enumerate(strategy_game_state.game_state.current_trick.cards)
            if card is not None
        )
        player_hand = tuple(
            sorted([str(card) for card in strategy_game_state.player_hand])
        )

        prev_tricks = tuple(
            (t.winner_index, t.score)
            for t in strategy_game_state.game_state.previous_tricks
        )

        return (
            current_trick,
            player_hand,
            prev_tricks,
            strategy_game_state.player_score,
        )


# Helper function to group equivalent moves
def group_equivalent_moves(cards: List[Card]) -> List[Card]:
    """Group equivalent moves to reduce the search space."""
    if not cards:
        return []

    # For Hearts, cards of the same suit with consecutive ranks are often equivalent
    # This is a simplified grouping that can be enhanced based on game state
    grouped = []
    by_suit = defaultdict(list)

    # Group cards by suit
    for card in cards:
        by_suit[card.suit].append(card)

    # Process each suit
    for suit, suit_cards in by_suit.items():
        # Sort by rank
        suit_cards.sort(key=lambda c: c.rank)

        # Add the lowest card of each suit
        if suit_cards:
            grouped.append(suit_cards[0])

        # Add the highest card of each suit if different from lowest
        if len(suit_cards) > 1 and suit_cards[-1].rank != suit_cards[0].rank:
            grouped.append(suit_cards[-1])

        # Add the Queen of Spades specifically (important in Hearts)
        queen_of_spades = next(
            (c for c in suit_cards if c.suit == "S" and c.rank == 12), None
        )
        if queen_of_spades and queen_of_spades not in grouped:
            grouped.append(queen_of_spades)

    # If we didn't reduce the number of cards, just return the original list
    if len(grouped) >= len(cards):
        return cards

    return grouped
