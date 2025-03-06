import json
import os
import sys
from typing import List, Optional

import pygame
from animation_manager import AnimationManager
from card import Card
from card_sprite import CardSprite
from event_handler import EventHandler
from game_renderer import GameRenderer
from game_state import GameState
from hearts_game import HeartsGame, Player
from layout_manager import LayoutManager
from strategies import (
    AggressiveStrategy,
    AvoidPointsStrategy,
    HumanStrategy,
    RandomStrategy,
    ReplayStrategy,
)

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60
AUTO_PLAY_DELAY = 500  # milliseconds


class GameVisualizer:
    def __init__(self, game_file: Optional[str] = None):
        # Initialize display
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hearts Game")
        self.clock = pygame.time.Clock()

        # Create game with appropriate players
        players = self._create_players(game_file)
        self.game = HeartsGame(players)

        # Initialize managers
        self.layout = LayoutManager(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.game_state = GameState(self.game)
        self.animation_mgr = AnimationManager()
        self.renderer = GameRenderer(self.screen, self.layout)
        self.event_handler = EventHandler(
            self.game_state,
            self.game,
            self.layout,
            lambda card: self.play_card(card),
        )

    def _create_players(self, game_file: Optional[str]) -> List[Player]:
        if game_file:
            return self._create_replay_players(game_file)
        return [
            Player("You", HumanStrategy()),
            Player("Bob", AvoidPointsStrategy()),
            Player("Charlie", AggressiveStrategy()),
            Player("AI", RandomStrategy()),
            # Player("AI", AIStrategy()),
        ]

    def _create_replay_players(self, game_file: str) -> List[Player]:
        print(f"Loading game from {game_file}")
        with open(game_file, "r") as f:
            games_data = json.load(f)
            print("Game data structure:", json.dumps(games_data, indent=2))

        game_data = games_data[0]  # First game only for now
        player_moves = [[] for _ in range(4)]

        for trick in game_data["tricks"]:
            for card_info in trick["cards"]:
                player_idx = card_info["player_index"]
                card = card_info["card"]
                player_moves[player_idx].append(card)

        return [
            Player(f"Player {i}", ReplayStrategy(player_moves[i])) for i in range(4)
        ]

    def _handle_play(self):
        if self.game.current_player_is_human:
            return

        played_card = self.game.choose_card(self.game.current_player_index)
        self.play_card(played_card)

    def play_card(self, played_card: Card):
        current_time = pygame.time.get_ticks()

        if current_time - self.game_state.last_auto_play <= AUTO_PLAY_DELAY:
            return

        if self.animation_mgr.has_moving_cards():
            return

        if self.game.current_trick.is_empty:
            self.animation_mgr.clear_animations()

        card_idx = self.game.hands[self.game.current_player_index].index(played_card)

        start_pos = self.layout.get_hand_position(
            self.game.current_player_index, card_idx
        )
        target_pos = self.layout.get_trick_position(self.game.current_player_index)

        sprite = CardSprite(played_card)
        self.animation_mgr.add_card_animation(sprite, start_pos, target_pos)
        self.game_state.last_auto_play = current_time

        self.game.play_card(played_card)

        if self.game.current_trick.is_empty:
            self.game_state.paused = True

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
            self.renderer.render_frame(self.game_state, self.game, self.animation_mgr)

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
