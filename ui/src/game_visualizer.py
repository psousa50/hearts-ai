import json
import os
import sys
from typing import List, Optional

import pygame
from animation_manager import AnimationManager
from card_sprite import CardSprite
from event_handler import EventHandler
from game_renderer import GameRenderer
from game_state import GameState
from hearts_game import HeartsGame, Player
from layout_manager import LayoutManager
from strategies import (
    AggressiveStrategy,
    AIStrategy,
    AvoidPointsStrategy,
    HumanStrategy,
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
        game = HeartsGame(players)

        # Initialize managers
        self.layout = LayoutManager(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.game_state = GameState(game)
        self.animation_mgr = AnimationManager()
        self.renderer = GameRenderer(self.screen, self.layout)
        self.event_handler = EventHandler(self.game_state, self.layout)

    def _create_players(self, game_file: Optional[str]) -> List[Player]:
        if game_file:
            return self._create_replay_players(game_file)
        return [
            Player("You", HumanStrategy()),
            Player("Bob", AvoidPointsStrategy()),
            Player("Charlie", AggressiveStrategy()),
            Player("AI", AIStrategy()),
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
        """Handle AI player moves"""
        current_time = pygame.time.get_ticks()

        if current_time - self.game_state.last_auto_play <= AUTO_PLAY_DELAY:
            return

        if self.animation_mgr.has_moving_cards():
            return

        current_player_index = self.game_state.current_player_index
        hand = self.game_state.hands[current_player_index]
        print("current player", current_player_index)
        print("hand", hand)

        # Play the card
        played_card, card_idx = self.game_state.play_card(current_player_index)
        if played_card is not None:
            # Create card animation
            print("playing card", played_card.rank, played_card.suit)
            start_pos = self.layout.get_hand_position(current_player_index, card_idx)
            target_pos = self.layout.get_trick_position(current_player_index)

            sprite = CardSprite(played_card)
            self.animation_mgr.add_card_animation(sprite, start_pos, target_pos)
            self.game_state.last_auto_play = current_time

            # Update AI state
            for player in self.game_state.players:
                if isinstance(player.strategy, AIStrategy):
                    player.strategy.current_trick_cards.append(
                        (played_card.suit, played_card.rank)
                    )
                    player.strategy.current_trick_cards_raw.append(
                        (played_card.suit, played_card.rank, current_player_index)
                    )

    def _handle_trick_completion(self):
        """Handle completion of tricks"""
        if len(self.game_state.current_trick_cards) == 4:
            if self.animation_mgr.has_moving_cards():
                return

            # Calculate points
            points = sum(
                1
                if card.suit == "H"
                else 13
                if card.suit == "S" and card.rank == 12
                else 0
                for card, _ in self.game_state.current_trick_cards
            )

            # Find winner
            lead_suit = self.game_state.current_trick_cards[0][0].suit
            followed_suit = [
                (card, player)
                for card, player in self.game_state.current_trick_cards
                if card.suit == lead_suit
            ]
            highest_card = max(
                followed_suit if followed_suit else self.game_state.current_trick_cards,
                key=lambda x: x[0].rank,
            )
            winner = highest_card[1]

            # Update AI state
            for player in self.game_state.players:
                if isinstance(player.strategy, AIStrategy):
                    player.strategy.update_game_state(True, winner)

            # Complete the trick
            self.game_state.game.complete_trick()
            self.animation_mgr.clear_animations()
            self.game_state.trick_completed = True
            self.game_state.paused = True

    def _handle_game_over(self):
        """Handle game over state"""
        if not self.game_state.is_game_over():
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.game_state.last_auto_play <= AUTO_PLAY_DELAY * 2:
            return

        # Reset game state
        self.game_state.reset_game()
        self.animation_mgr.clear_animations()

        # Reset AI game state
        for player in self.game_state.players:
            if isinstance(player.strategy, AIStrategy):
                player.strategy.game_id += 1
                player.strategy.trick_number = 0
                player.strategy.previous_tricks = []
                player.strategy.current_trick_cards = []

        self.game_state.last_auto_play = current_time

    def update(self):
        """Update game state"""
        if self.game_state.paused:
            return

        # Handle trick completion
        self._handle_trick_completion()

        self._handle_play()

        # Handle game over
        self._handle_game_over()

        # Update animations
        self.animation_mgr.update_animations()

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
