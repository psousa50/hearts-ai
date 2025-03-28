import sys
import copy
import numpy as np
from functools import lru_cache
from collections import defaultdict

from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState
from hearts_game_core.game_core import HeartsGame, Player
from hearts_game_core.deck import Deck
from strategies.random import RandomStrategy

DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force output to be displayed immediately

class SimulationStrategy(Strategy):
    def __init__(self, num_simulations: int = 5000, early_stopping: bool = False):
        self.num_simulations = num_simulations
        self.early_stopping = early_stopping
        self.move_cache = {}
        self.all_cards = Deck(shuffle=False).cards
        
    
    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        # Fast path for single valid move
        if len(strategy_game_state.valid_moves) == 1:
            return strategy_game_state.valid_moves[0]
        
        # Check cache for this game state
        cache_key = self._get_cache_key(strategy_game_state)
        if cache_key in self.move_cache:
            debug_print(f"Cache hit for {cache_key}")
            return self.move_cache[cache_key]
        
        current_player_idx = strategy_game_state.player_index
        current_score = strategy_game_state.player_score
        
        # Determine number of simulations based on game state
        trick_number = len(strategy_game_state.game_state.previous_tricks) + 1
        debug_print(f"------------------------ Trick number: {trick_number} ------------------------")
        cards_left = len(strategy_game_state.player_hand)
        
        # Adaptive simulation count - fewer simulations needed in late game
        if cards_left <= 3:
            # Late game - we can do more exhaustive search with fewer simulations
            num_simulations = max(50, self.num_simulations // 5)
        else:
            num_simulations = self.num_simulations
        
        # Distribute simulations evenly among moves
        simulations_per_move = max(1000, num_simulations // len(strategy_game_state.valid_moves))
        debug_print(f"Distributing {num_simulations} simulations evenly among {len(strategy_game_state.valid_moves)} moves: {simulations_per_move} simulations per move")
        
        # Track scores for each move
        move_scores = {str(move): [] for move in strategy_game_state.valid_moves}
        best_move = None
        best_added_score = float('inf')
        
        first_player_index = strategy_game_state.game_state.current_trick.first_player_index
        
        # Collect all played cards once
        all_played_cards = []
        for previous_trick in strategy_game_state.game_state.previous_tricks:
            all_played_cards.extend(previous_trick.cards)
        
        for card in strategy_game_state.game_state.current_trick.cards:
            if card is not None:
                all_played_cards.append(card)
        
        # Add current player's hand
        all_played_cards.extend(strategy_game_state.player_hand)
        
        # Get all remaining cards
        all_cards_in_players_hands = [card for card in self.all_cards if card not in all_played_cards]
        
        # Run simulations for each move
        for move in strategy_game_state.valid_moves:
            move_str = str(move)
            # Run multiple simulations for this move
            total_added_score = 0
            
            for _ in range(simulations_per_move):
                # Create a new game for simulation
                sim_game = self._create_game_for_simulation(
                    strategy_game_state, 
                    first_player_index,
                    current_player_idx, 
                    all_cards_in_players_hands.copy()
                )
                
                # Play the move and complete the game
                sim_game.play_card(move)
                sim_completed_game = sim_game.play_game()
                
                # Calculate score difference
                player_score = sim_completed_game.players[current_player_idx].score
                added_score = player_score - current_score
                
                move_scores[move_str].append(added_score)
                total_added_score += added_score

                # Early stopping check after a minimum number of simulations
                if self.early_stopping and len(move_scores[move_str]) >= 10:
                    avg_score = total_added_score / len(move_scores[move_str])
                    if best_move is not None and avg_score > best_added_score * 1.2:
                        # This move is clearly worse, stop simulating it
                        break
            
            # Calculate average score for this move
            if move_scores[move_str]:
                avg_score = total_added_score / len(move_scores[move_str])
                debug_print(f"{move_str}: {avg_score:.2f}")
                
                # Update best move if this is better
                if avg_score < best_added_score:
                    best_added_score = avg_score
                    best_move = move
        
        # If no best move was found, use the first valid move
        if best_move is None:
            best_move = strategy_game_state.valid_moves[0]

        debug_print(f"Best move: {best_move} with added score: {best_added_score:.2f}")        
        # Cache the result
        self.move_cache[cache_key] = best_move
        
        return best_move
    
    def _get_cache_key(self, strategy_game_state):
        """Create a cache key based on the current game state"""
        # Include current trick, player hand, and previous tricks in the key
        current_trick = tuple((i, str(card)) for i, card in enumerate(strategy_game_state.game_state.current_trick.cards) if card is not None)
        player_hand = tuple(sorted([str(card) for card in strategy_game_state.player_hand]))
        
        # Include a simplified version of previous tricks (just the winner and score)
        prev_tricks = tuple((t.winner_index, t.score) for t in strategy_game_state.game_state.previous_tricks)
        
        return (current_trick, player_hand, prev_tricks)
    
    def _create_game_for_simulation(self, strategy_game_state, first_player_index, current_player_idx, all_cards_in_players_hands):
        """Create a game for simulation with optimized setup"""
        # Create players with random strategies
        players = [Player(f"Random{i}", RandomStrategy()) for i in range(4)]
        game = HeartsGame(players)
        
        # Set up the game state
        game.current_state = copy.deepcopy(strategy_game_state.game_state)
        game.players[current_player_idx].hand = strategy_game_state.player_hand.copy()
        game.players[current_player_idx].score = strategy_game_state.player_score
        
        # Shuffle remaining cards
        np.random.shuffle(all_cards_in_players_hands)
        
        # Distribute cards to other players
        cards_index = 0
        for player_idx in range(4):
            if player_idx != current_player_idx:
                cards_to_distribute = len(strategy_game_state.player_hand)
                if self._has_played(first_player_index, current_player_idx, player_idx):
                    cards_to_distribute -= 1
                
                # Ensure we don't go out of bounds
                if cards_index + cards_to_distribute <= len(all_cards_in_players_hands):
                    game.players[player_idx].hand = all_cards_in_players_hands[cards_index:cards_index + cards_to_distribute]
                    cards_index += cards_to_distribute
                else:
                    # If we don't have enough cards, just use what's left
                    game.players[player_idx].hand = all_cards_in_players_hands[cards_index:]
                    cards_index = len(all_cards_in_players_hands)
        
        return game
    
    def _has_played(self, first_player_index, current_player_index, other_player_index):
        """Determine if a player has already played in the current trick"""
        players_played = (current_player_index - first_player_index) % 4
        other_player_position = (other_player_index - first_player_index) % 4
        return other_player_position < players_played
