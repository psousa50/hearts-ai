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
from hearts_game_core.game_core import HeartsGame, Player
from hearts_game_core.game_models import Card, CompletedTrick
from layout_manager import LayoutManager
from strategies import (
    AIStrategy,
    HumanStrategy,
    MyStrategy,
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
        self.replaying_games = game_file is not None
        players = (
            self._create_players()
            if not self.replaying_games
            else self._create_replay_players(game_file)
        )
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

    def _create_players(self) -> List[Player]:
        return self._create_all_players()

    def _create_all_players(self) -> List[Player]:
        return [
            Player("Human", HumanStrategy()),
            Player("AI", AIStrategy()),
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

    def _create_replay_players(self, game_file: str) -> List[Player]:
        print(f"Loading game from {game_file}")
        with open(game_file, "r") as f:
            games_data = json.load(f)
        print(f"Loaded {len(games_data)} moves")

        game_data = games_data[0]  # First game only for now
        player_moves = [[] for _ in range(4)]

        for trick in game_data["previous_tricks"]:
            for i, card_dict in enumerate(trick["cards"]):
                card = Card(card_dict["suit"], card_dict["rank"])
                player_moves[i].append(card)

        player_scores = [p["score"] for p in game_data["players"]]

        # Create a temporary game to initialize the GameMovesFilter
        temp_game = HeartsGame(
            [Player(f"Player {i}", RandomStrategy()) for i in range(4)]
        )
        temp_game.scores = player_scores

        # Create the filter and get the good player indexes
        self.game_filter = GameMovesFilter(temp_game)

        player_hands = [p["initial_hand"] for p in game_data["players"]]
        player_hands = [
            [Card(card["suit"], card["rank"]) for card in hand] for hand in player_hands
        ]
        for hand in player_hands:
            hand.sort(key=lambda c: (c.suit, c.rank))

        players = [
            Player(f"Player {i}", ReplayStrategy(player_moves[i]), player_hands[i])
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

        card_idx = self.game.hands[self.game.current_player_index].index(played_card)

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
