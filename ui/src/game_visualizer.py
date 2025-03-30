import json
import os
import sys
from typing import List, Optional

import pygame
from animation_manager import AnimationManager
from card_sprite import CardSprite
from event_handler import EventHandler
from game_moves_filter import GameMovesFilter
from game_renderer import GameRenderer
from game_state import GameState
from layout_manager import LayoutManager

from hearts_game_core.game_core import HeartsGame, Player
from hearts_game_core.game_models import Card, CompletedGame, CompletedTrick
from strategies.aggressive import AggressiveStrategy
from strategies.ai import AIStrategy
from strategies.human import HumanStrategy
from strategies.monte_carlo import MonteCarloStrategy
from strategies.my import MyStrategy
from strategies.random import RandomStrategy
from strategies.replay import ReplayStrategy
from strategies.simulation import SimulationStrategy

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60
AUTO_PLAY_DELAY = 500  # milliseconds


class GameVisualizer:
    def __init__(self, game_file: Optional[str] = None):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hearts Game")
        self.clock = pygame.time.Clock()

        self.replaying_games = game_file is not None
        players = (
            self._create_players()
            if not self.replaying_games
            else self._create_replay_players(game_file)
        )
        self.game = HeartsGame(players)

        self.layout = LayoutManager(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.game_state = GameState(self.game)
        self.animation_mgr = AnimationManager()
        self.renderer = GameRenderer(self.screen, self.layout)
        self.event_handler = EventHandler(
            self.game_state,
            self.layout,
            lambda card: self.play_card(card),
        )

    def _create_players(self) -> List[Player]:
        return self._create_monte_carlo_players()

    def _create_all_simulations(self) -> List[Player]:
        return [
            Player("Sim 1", SimulationStrategy()),
            Player("Sim 2", SimulationStrategy()),
            Player("Sim 3", SimulationStrategy()),
            Player("Sim 4", SimulationStrategy()),
        ]

    def _create_all_players(self) -> List[Player]:
        return [
            Player("Human", HumanStrategy()),
            Player("AI", AIStrategy()),
            Player("My Strategy", MyStrategy()),
            Player("Random", RandomStrategy()),
        ]

    def _create_all_players_no_ai(self) -> List[Player]:
        return [
            Player("Aggressive", AggressiveStrategy()),
            Player("Simulation", SimulationStrategy()),
            Player("My Strategy", MyStrategy()),
            Player("Random", RandomStrategy()),
        ]

    def _create_human_players(self) -> List[Player]:
        return [
            Player("Human 1", HumanStrategy()),
            Player("Human 2", HumanStrategy()),
            Player("Human 3", HumanStrategy()),
            Player("Human 4", HumanStrategy()),
        ]

    def _create_ai_players(self) -> List[Player]:
        return [
            Player("AI 1", AIStrategy()),
            Player("AI 2", AIStrategy()),
            Player("AI 3", AIStrategy()),
            Player("AI 4", AIStrategy()),
        ]

    def _create_ai_players_and_human(self) -> List[Player]:
        return [
            Player("Human 1", HumanStrategy()),
            Player("AI 2", AIStrategy()),
            Player("AI 3", AIStrategy()),
            Player("AI 4", AIStrategy()),
        ]

    def _create_my_strategies(self) -> List[Player]:
        return [
            Player("My Strategy 1", MyStrategy()),
            Player("My Strategy 2", MyStrategy()),
            Player("My Strategy 3", MyStrategy()),
            Player("My Strategy 4", MyStrategy()),
        ]

    def _create_simulation_players(self) -> List[Player]:
        return [
            Player("Simulation 1", SimulationStrategy()),
            Player("Simulation 2", SimulationStrategy()),
            Player("Simulation 3", SimulationStrategy()),
            Player("Simulation 4", SimulationStrategy()),
        ]

    def _create_monte_carlo_players(self) -> List[Player]:
        return [
            Player("Monte Carlo 1", MonteCarloStrategy()),
            Player("Monte Carlo 2", MonteCarloStrategy()),
            Player("Monte Carlo 3", MonteCarloStrategy()),
            Player("Monte Carlo 4", MonteCarloStrategy()),
        ]

    def _create_replay_players(self, game_file: str) -> List[Player]:
        with open(game_file, "r") as f:
            all_games_data = json.load(f)
            completed_games = [CompletedGame.parse_obj(game) for game in all_games_data]
        print(f"Loaded {len(completed_games)} games")

        completed_game = completed_games[0]  # First game only for now

        player_moves = [[] for _ in range(4)]
        for trick in completed_game.completed_tricks:
            for i, card in enumerate(trick.cards):
                player_moves[i].append(card)

        self.game_filter = GameMovesFilter(completed_game)

        players = [
            Player(
                f"Player {i}",
                ReplayStrategy(player_moves[i]),
                initial_hand=completed_game.players[i].initial_hand,
            )
            for i in range(4)
        ]

        return players

    def _handle_play(self):
        if self.game_state.current_player_is_human:
            return

        current_time = pygame.time.get_ticks()

        if current_time - self.game_state.last_auto_play <= AUTO_PLAY_DELAY:
            return

        if self.animation_mgr.has_moving_cards():
            return

        if self.game.current_trick.is_empty:
            self.animation_mgr.clear_animations()

        played_card = self.game.choose_card(self.game.current_player_index)
        self.play_card(played_card)

        self.game_state.last_auto_play = current_time

    def play_card(self, played_card: Card):
        self.game_state.paused = False
        if self.game.current_trick.is_empty:
            self.animation_mgr.clear_animations()

        hands = [p.hand for p in self.game.players]
        card_idx = hands[self.game.current_player_index].index(played_card)

        start_pos = self.layout.get_hand_position(
            self.game.current_player_index, card_idx
        )
        target_pos = self.layout.get_trick_position(self.game.current_player_index)

        sprite = CardSprite(played_card, self.game.current_player_index)
        self.animation_mgr.add_card_animation(sprite, start_pos, target_pos)

        self.game.play_card(played_card)

        if self.game.current_trick.is_empty:
            previous_trick = self.game.previous_tricks[-1]
            if self.replaying_games:
                for card in self.animation_mgr.get_cards_in_play():
                    card.good_move = self.is_good_move(
                        card.player_index, previous_trick
                    )
            self.game_state.paused = True

    def is_good_move(self, player_index: int, trick: CompletedTrick) -> bool:
        return self.game_filter.filter(player_index, trick)

    def _handle_game_over(self):
        """Handle game over state"""
        if not self.game.is_game_over():
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.game_state.last_auto_play <= AUTO_PLAY_DELAY * 2:
            return

        # Reset game state
        self.game_state.reset_game()
        self.animation_mgr.clear_animations()

        self.game_state.last_auto_play = current_time

    def update(self):
        self.animation_mgr.update_animations()

        if self.game_state.paused:
            return

        self._handle_play()

        # Handle game over
        self._handle_game_over()

    def run(self):
        """Main game loop"""
        running = True
        while running:
            self.clock.tick(FPS)
            running = self.event_handler.handle_events()
            self.update()
            self.renderer.render_frame(self.game_state, self.animation_mgr)

        pygame.quit()


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Usage:")
        print("  python game_visualizer.py")
        print("  python game_visualizer.py <game_file.json>")
        sys.exit(1)

    if len(sys.argv) == 1:
        visualizer = GameVisualizer()
    else:
        game_file = sys.argv[1]
        if not os.path.exists(game_file):
            print(f"Error: File {game_file} not found")
            sys.exit(1)
        visualizer = GameVisualizer(game_file)

    visualizer.run()
