import copy
import os
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from itertools import islice
from typing import List

from hearts_game_core.deck import Deck
from hearts_game_core.game_core import HeartsGame, Player
from hearts_game_core.game_models import Card
from hearts_game_core.random_manager import RandomManager
from hearts_game_core.strategies import Strategy, StrategyGameState
from strategies.random import RandomStrategy

DEBUG = False


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force output to be displayed immediately


class SimulationStrategy(Strategy):
    def __init__(self, num_simulations: int = 5000, random_manager: RandomManager = None):
        self.random_manager = random_manager if random_manager is not None else RandomManager()
        self.num_simulations = num_simulations
        self.move_cache = {}
        self.deck = Deck(shuffle=False, random_manager=self.random_manager)
        self.all_cards = self.deck.cards
        self.number_of_processes = os.cpu_count()
        self.executor = ProcessPoolExecutor(max_workers=self.number_of_processes)

    def batch_moves(self, moves: list[Card], size: int) -> list[Card]:
        it = iter(moves)
        while chunk := list(islice(it, size)):
            yield chunk

    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        valid_moves = strategy_game_state.valid_moves
        if len(valid_moves) == 1:
            return valid_moves[0]

        debug_print(f"Valid moves: {" ".join([str(card) for card in valid_moves])}")
        grouped_valid_moves = group_equivalent_moves(valid_moves)
        debug_print(f"Grouped valid moves: {" ".join([str(card) for card in grouped_valid_moves])}")

        # Check cache for this game state
        # cache_key = self._get_cache_key(strategy_game_state)
        # if cache_key in self.move_cache:
        #     debug_print(f"Cache hit for {cache_key}")
        #     return self.move_cache[cache_key]

        trick_number = len(strategy_game_state.game_state.previous_tricks) + 1
        debug_print(f"------------------------ Trick number: {trick_number} ------------------------")

        cards_left = len(strategy_game_state.player_hand)
        if cards_left <= 3:
            # Late game - we can do more exhaustive search with fewer simulations
            num_simulations = max(50, self.num_simulations // 5)
        else:
            num_simulations = self.num_simulations

        simulations_per_move = max(1000, num_simulations // len(valid_moves))

        all_played_cards = []
        for previous_trick in strategy_game_state.game_state.previous_tricks:
            all_played_cards.extend(previous_trick.cards)

        for card in strategy_game_state.game_state.current_trick.cards:
            if card is not None:
                all_played_cards.append(card)

        all_played_cards.extend(strategy_game_state.player_hand)

        all_cards_in_players_hands = [card for card in self.all_cards if card not in all_played_cards]

        best_move = None
        best_added_score_all = 10000

        for moves in self.batch_moves(grouped_valid_moves, self.number_of_processes):
            futures = [
                self.executor.submit(
                    run_simulations_for_move,
                    strategy_game_state,
                    move,
                    simulations_per_move,
                    all_cards_in_players_hands,
                    self.deck,
                    self.random_manager,
                )
                for move in moves
            ]
            results = [future.result() for future in futures]
            best_move, best_added_score = min(results, key=lambda x: x[1])
            if best_added_score < best_added_score_all:
                best_added_score_all = best_added_score
                best_move = best_move

        debug_print(f"Best move: {best_move} with added score: {best_added_score_all:.2f}")

        if best_move is None:
            best_move = strategy_game_state.valid_moves[0]

        # self.move_cache[cache_key] = best_move
        return best_move

    def _get_cache_key(self, strategy_game_state):
        current_trick = tuple(
            (i, str(card)) for i, card in enumerate(strategy_game_state.game_state.current_trick.cards) if card is not None
        )
        player_hand = tuple(sorted([str(card) for card in strategy_game_state.player_hand]))

        prev_tricks = tuple((t.winner_index, t.score) for t in strategy_game_state.game_state.previous_tricks)

        return (current_trick, player_hand, prev_tricks)


def create_game_for_simulation(
    strategy_game_state,
    first_player_index,
    current_player_idx,
    all_cards_in_players_hands,
    deck,
    random_manager: RandomManager,
):
    players = [Player(f"Random{i}", RandomStrategy(random_manager=random_manager)) for i in range(4)]
    game = HeartsGame(players, deck=deck, random_manager=random_manager)

    game.current_state = copy.deepcopy(strategy_game_state.game_state)
    game.players[current_player_idx].hand = strategy_game_state.player_hand.copy()
    game.players[current_player_idx].score = strategy_game_state.player_score

    random_manager.shuffle(all_cards_in_players_hands)

    initial_cards_to_distribute = len(strategy_game_state.player_hand)
    cards_index = 0
    for player_idx in range(4):
        if player_idx != current_player_idx:
            cards_to_distribute = initial_cards_to_distribute
            if _has_played(first_player_index, current_player_idx, player_idx):
                cards_to_distribute -= 1

            game.players[player_idx].hand = all_cards_in_players_hands[cards_index : cards_index + cards_to_distribute]
            cards_index += cards_to_distribute

    return game


def _has_played(first_player_index, current_player_index, other_player_index):
    players_played = (current_player_index - first_player_index) % 4
    other_player_position = (other_player_index - first_player_index) % 4
    return other_player_position < players_played


def run_simulations_for_move(
    strategy_game_state,
    move,
    simulations_per_move,
    all_cards_in_players_hands,
    deck,
    random_manager: RandomManager,
):
    first_player_index = strategy_game_state.game_state.current_trick.first_player_index
    current_player_idx = strategy_game_state.player_index
    average_added_score = 0

    for _ in range(simulations_per_move):
        sim_game = create_game_for_simulation(
            strategy_game_state,
            first_player_index,
            current_player_idx,
            all_cards_in_players_hands.copy(),
            deck,
            random_manager,
        )

        sim_game.play_card(move)
        sim_completed_game = sim_game.play_game()

        player_score_after_simulation = sim_completed_game.players[current_player_idx].score
        added_score = player_score_after_simulation - strategy_game_state.player_score

        average_added_score += added_score

    average_added_score /= simulations_per_move
    debug_print(f"{move}: avg {average_added_score:.2f}")

    return move, average_added_score


def group_equivalent_moves(cards: List[Card]) -> List[Card]:
    has_queen_of_spades = Card.QueenOfSpades in cards
    grouped_by_suit = defaultdict(list)

    # Group cards by suit
    for card in cards:
        grouped_by_suit[card.suit].append(card)

    result = []

    # For each suit group, sort by rank and keep highest card from each consecutive sequence
    for suit_cards in grouped_by_suit.values():
        suit_cards.sort(key=lambda c: c.rank)
        group = []

        for card in suit_cards:
            if not group:
                group.append(card)
            elif card.rank == group[-1].rank + 1:
                group[-1] = card  # Replace with higher card in sequence
            else:
                result.append(group[-1])
                group = [card]

        if group:
            result.append(group[-1])

    if has_queen_of_spades:
        result.append(Card.QueenOfSpades)

    return result
