import json
import os
import sys
from typing import List, Optional, Tuple

import pygame
from card_sprite import CARD_HEIGHT, CARD_WIDTH, CardSprite
from hearts_game import Card, HeartsGame, Player
from strategies import (
    AggressiveStrategy,
    AIStrategy,
    AvoidPointsStrategy,
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

# Colors
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)


class GameVisualizer:
    def __init__(self, game_file: Optional[str] = None):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hearts Game")
        self.clock = pygame.time.Clock()

        # Player positions (center points for names and scores)
        self.player_positions = {
            0: (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50),  # Bottom
            1: (200, WINDOW_HEIGHT // 2),  # Left
            2: (WINDOW_WIDTH // 2, 30),  # Top
            3: (WINDOW_WIDTH - 200, WINDOW_HEIGHT // 2),  # Right
        }

        # Hand display positions and offsets
        card_overlap = 30
        self.hand_positions = {
            0: {
                "start": (WINDOW_WIDTH // 4, WINDOW_HEIGHT - 200),  # Bottom
                "offset": (card_overlap, 0),
            },
            1: {
                "start": (100, WINDOW_HEIGHT // 4),  # Left - moved further right
                "offset": (0, card_overlap),
            },
            2: {
                "start": (WINDOW_WIDTH // 4, 70),  # Top
                "offset": (card_overlap, 0),
            },
            3: {
                "start": (WINDOW_WIDTH - 120, WINDOW_HEIGHT // 4),  # Right
                "offset": (0, card_overlap),
            },
        }

        self.cards_in_play: List[CardSprite] = []
        self.trick_center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        if game_file:
            print(f"Loading game from {game_file}")
            # Load game from file
            with open(game_file, "r") as f:
                games_data = json.load(f)
                print("Game data structure:", json.dumps(games_data, indent=2))

            # First game only for now
            game_data = games_data[0]

            # Extract all cards played by each player across all tricks
            player_moves = [[] for _ in range(4)]  # List of moves for each player
            for trick in game_data["tricks"]:
                for card_info in trick["cards"]:
                    player_idx = card_info["player_index"]
                    card = card_info["card"]
                    player_moves[player_idx].append(card)

            # Create replay strategies for each player
            players = [
                Player(f"Player {i}", ReplayStrategy(player_moves[i])) for i in range(4)
            ]
        else:
            players = [
                Player("You", RandomStrategy()),
                Player("Bob", AvoidPointsStrategy()),
                Player("Charlie", AggressiveStrategy()),
                Player("AI", AIStrategy()),
            ]

        # Create the game with the appropriate players
        self.game = HeartsGame(players)

        self.current_trick = 0
        self.current_card = 0
        self.auto_play = False
        self.last_auto_play = pygame.time.get_ticks()
        self.selected_card = None
        self.trick_completed = False
        self.trick_completion_time = 0
        self.paused = False  # New flag for pausing after tricks

    def clear_trick_cards(self):
        """Clear all cards from the current trick display"""
        self.cards_in_play = []

    def check_and_complete_trick(self):
        """Check if trick is complete and handle completion"""
        if len(self.game.current_trick) == 4:
            # Wait for any card animations to finish
            if any(card.moving for card in self.cards_in_play):
                return False

            # Calculate points for this trick
            points = 0
            for card, _ in self.game.current_trick:
                if card.suit == "H":
                    points += 1
                elif card.suit == "S" and card.rank == 12:  # Queen of Spades
                    points += 13

            # Find winner
            lead_suit = self.game.current_trick[0][0].suit
            followed_suit = [
                (card, player)
                for card, player in self.game.current_trick
                if card.suit == lead_suit
            ]
            highest_card = max(
                followed_suit if followed_suit else self.game.current_trick,
                key=lambda x: x[0].rank,
            )
            winner = highest_card[1]

            # Update AI state with trick completion
            for player in self.game.players:
                if isinstance(player.strategy, AIStrategy):
                    player.strategy.update_game_state(True, winner)

            # Complete the trick
            self.game.complete_trick()

            # Clear trick cards
            self.clear_trick_cards()

            # Update game state
            self.trick_completed = True
            self.paused = True
            return True

        return False

    def handle_click(self, pos):
        if self.game.current_player == 0:
            # Check if clicked on a card in the player's hand
            hand = self.game.hands[0]
            start_x, start_y = self.hand_positions[0]["start"]
            offset_x, _ = self.hand_positions[0]["offset"]

            # Check cards from right to left so we select the rightmost visible card
            for i in range(len(hand) - 1, -1, -1):
                card = hand[i]
                x = start_x + (i * offset_x)
                rect = pygame.Rect(x, start_y, CARD_WIDTH, CARD_HEIGHT)
                if rect.collidepoint(pos):
                    try:
                        played_card = self.game.play_card(0, card)
                        if played_card is not None:
                            sprite = CardSprite(played_card)
                            sprite.current_pos = (
                                x + CARD_WIDTH // 2,
                                start_y + CARD_HEIGHT // 2,
                            )
                            sprite.target_pos = self.get_trick_position(
                                len(self.game.current_trick) - 1, current_player=0
                            )
                            sprite.moving = True
                            self.cards_in_play.append(sprite)
                            self.last_auto_play = pygame.time.get_ticks()

                            # Update AI state with played card
                            for player in self.game.players:
                                if isinstance(player.strategy, AIStrategy):
                                    player.strategy.current_trick_cards = [
                                        (c.suit, c.rank)
                                        for c, _ in self.game.current_trick
                                    ]
                        break
                    except ValueError:
                        # Invalid move, ignore
                        pass

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.paused:  # Resume game when space is pressed
                        self.paused = False
                        self.clear_trick_cards()
                        self.trick_completed = False
                        self.last_auto_play = pygame.time.get_ticks()
                if event.key == pygame.K_RETURN:
                    self.auto_play = (
                        not self.auto_play
                    )  # Toggle auto-play if not paused
                elif event.key == pygame.K_ESCAPE:
                    return False
        return True

    def update(self):
        """Update game state"""
        if self.paused:
            return

        current_time = pygame.time.get_ticks()

        if self.trick_completed:
            # Check if any cards are still moving
            if any(card.moving for card in self.cards_in_play):
                return

            # Clear cards in play
            self.cards_in_play = []
            self.trick_completed = False
            self.paused = False

        # Check if it's AI's turn
        if (
            self.game.current_player != 0
            and current_time - self.last_auto_play > AUTO_PLAY_DELAY
        ):  # Player 0 is human
            # Get current player's hand and valid moves
            hand = self.game.hands[self.game.current_player]
            valid_moves = self.game.get_valid_moves(self.game.current_player)

            # Let AI choose a card
            strategy = self.game.players[self.game.current_player].strategy
            card = strategy.choose_card(hand, valid_moves)

            # Find card index in hand
            try:
                card_idx = hand.index(card)
            except ValueError:
                print(f"AI tried to play invalid card: {card}")
                print(f"Valid moves: {valid_moves}")
                print(f"Hand: {hand}")
                return

            # Play the card
            played_card = self.game.play_card(self.game.current_player, card)
            if played_card is not None:
                start_x, start_y = self.hand_positions[self.game.current_player][
                    "start"
                ]
                offset_x, offset_y = self.hand_positions[self.game.current_player][
                    "offset"
                ]
                sprite = CardSprite(played_card)
                sprite.current_pos = (
                    start_x + (card_idx * offset_x) + CARD_WIDTH // 2,
                    start_y + (card_idx * offset_y) + CARD_HEIGHT // 2,
                )
                sprite.target_pos = self.get_trick_position(
                    len(self.game.current_trick) - 1,
                    current_player=self.game.current_player,
                )
                sprite.moving = True
                self.cards_in_play.append(sprite)
                self.last_auto_play = current_time

                # Update AI state with played card
                for player in self.game.players:
                    if isinstance(player.strategy, AIStrategy):
                        player.strategy.current_trick_cards.append(
                            (card.suit, card.rank)
                        )
                        player.strategy.current_trick_cards_raw.append(
                            (card.suit, card.rank, self.game.current_player)
                        )

                # Check if trick is complete
                self.check_and_complete_trick()

        # Only auto-play for AI players or if auto_play is explicitly enabled
        if self.game.current_player != 0 or (
            self.auto_play and self.game.current_player == 0
        ):
            if pygame.time.get_ticks() - self.last_auto_play > AUTO_PLAY_DELAY:
                # Wait for any card animations to finish before checking trick completion
                if any(card.moving for card in self.cards_in_play):
                    return

                trick_completed = self.check_and_complete_trick()
                # Check if trick is complete
                if trick_completed:
                    return

                # If this is the start of a new trick, clear any remaining cards
                if len(self.game.current_trick) == 0:
                    self.clear_trick_cards()

                # Play next card
                current_player = self.game.current_player
                card = self.game.play_card(current_player)
                start_pos = self.hand_positions[current_player]["start"]
                sprite = CardSprite(card)
                sprite.current_pos = (
                    start_pos[0] + CARD_WIDTH // 2,
                    start_pos[1] + CARD_HEIGHT // 2,
                )
                sprite.target_pos = self.get_trick_position(
                    len(self.game.current_trick) - 1, current_player=current_player
                )
                sprite.moving = True
                self.cards_in_play.append(sprite)

                # Update AI state with played card
                for player in self.game.players:
                    if isinstance(player.strategy, AIStrategy):
                        player.strategy.current_trick_cards_raw.append(
                            (card.suit, card.rank, current_player)
                        )
                self.last_auto_play = pygame.time.get_ticks()

        # Check for game over
        if self.game.game_over():
            # Start a new game after a delay
            if pygame.time.get_ticks() - self.last_auto_play > AUTO_PLAY_DELAY * 2:
                self.game.reset_game()
                self.clear_trick_cards()
                self.trick_completed = False
                self.paused = False
                self.auto_play = False  # Turn off auto-play when game resets
                # Reset AI game state
                for _, strategy in self.game.players:
                    if isinstance(strategy, AIStrategy):
                        strategy.game_id += 1
                        strategy.trick_number = 0
                        strategy.previous_tricks = []
                        strategy.current_trick_cards = []
                self.last_auto_play = pygame.time.get_ticks()

        # Update card animations
        moving_cards = []
        for card in self.cards_in_play:
            if card.moving:
                card.move_towards_target()
                moving_cards.append(card)
            elif (
                not self.trick_completed
            ):  # Only keep non-moving cards if trick is not completed
                moving_cards.append(card)
        self.cards_in_play = moving_cards

    def get_trick_position(
        self, card_index: int, current_player: Optional[int] = None
    ) -> Tuple[int, int]:
        # Get the player who played this card
        if current_player is not None:
            # Use the provided player index for cards being played
            player_idx = current_player
        else:
            # In current_trick, each entry is (card, player_idx)
            player_idx = self.game.current_trick[card_index][1]

        # Get center position and player position
        center_x, center_y = self.trick_center
        player_x, player_y = self.player_positions[player_idx]

        # Calculate the position based on the player's location
        offset = 80  # Distance from center
        if player_idx == 0:  # Bottom
            x = center_x
            y = center_y + offset
        elif player_idx == 1:  # Left
            x = center_x - offset
            y = center_y
        elif player_idx == 2:  # Top
            x = center_x
            y = center_y - offset
        else:  # Right
            x = center_x + offset
            y = center_y

        return (int(x), int(y))

    def draw_player_hand(
        self, player_idx: int, hand: List[Card], highlight_valid: bool = False
    ):
        pos = self.hand_positions[player_idx]
        start_x, start_y = pos["start"]
        offset_x, offset_y = pos["offset"]

        valid_moves = self.game.get_valid_moves(player_idx) if highlight_valid else []

        for i, card in enumerate(hand):
            sprite = CardSprite(card)
            x = start_x + (i * offset_x)
            y = start_y + (i * offset_y)

            # Highlight valid moves for human player
            if highlight_valid and card in valid_moves:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 0),
                    (x - 3, y - 3, CARD_WIDTH + 6, CARD_HEIGHT + 6),
                )

            self.screen.blit(sprite.image, (x, y))

    def get_current_trick(self):
        if self.current_trick >= len(self.game.tricks):
            return []
        return self.game.tricks[self.current_trick]

    def draw(self):
        self.screen.fill(GREEN)

        scores = self.game.scores
        players = self.game.players

        # Draw player positions and scores
        font = pygame.font.Font(None, 36)
        medium_font = pygame.font.Font(None, 24)

        for i, player in enumerate(players):
            pos = self.player_positions[i]

            # Create background rectangle for player info
            name_text = player.name
            strategy_text = f"({player.strategy.__class__.__name__})"
            score_text = str(scores[i])

            name_surface = font.render(name_text, True, WHITE)
            strategy_surface = medium_font.render(strategy_text, True, WHITE)
            score_surface = font.render(score_text, True, WHITE)

            name_rect = name_surface.get_rect(center=(pos[0], pos[1] - 15))
            strategy_rect = strategy_surface.get_rect(center=(pos[0], pos[1] + 5))
            score_rect = score_surface.get_rect(center=(pos[0], pos[1] + 30))

            # Calculate background rectangle to fit all elements
            bg_rect = pygame.Rect(
                0,
                0,
                max(name_rect.width, strategy_rect.width, score_rect.width) + 20,
                name_rect.height + strategy_rect.height + score_rect.height + 25,
            )
            bg_rect.center = (pos[0], pos[1] + 5)

            pygame.draw.rect(self.screen, DARK_GREEN, bg_rect)
            self.screen.blit(name_surface, name_rect)
            self.screen.blit(strategy_surface, strategy_rect)
            self.screen.blit(score_surface, score_rect)

        # Draw current hands for all players
        for i in range(4):
            self.draw_player_hand(
                i, self.game.hands[i], i == 0 and self.game.current_player == 0
            )

        # Draw cards in play
        for card in self.cards_in_play:
            card.move_towards_target()
            self.screen.blit(card.image, card.rect)

        # Draw game info
        game_info = f"Current Player: {players[self.game.current_player].name}"
        if len(self.game.current_trick) > 0:
            game_info += f" - Cards in trick: {len(self.game.current_trick)}/4"

        info_text = font.render(game_info, True, WHITE)
        self.screen.blit(info_text, (10, 10))

        # Draw controls info
        controls = [
            "Controls:",
            "Space - Toggle auto-play",
            "Click card to play (when it's your turn)",
            "Close window to quit",
        ]
        small_font = pygame.font.Font(None, 24)
        for i, control in enumerate(controls):
            control_text = small_font.render(control, True, WHITE)
            self.screen.blit(
                control_text, (10, WINDOW_HEIGHT - 20 * (len(controls) - i))
            )

        # Draw debug info in bottom right corner
        debug_font = pygame.font.Font(None, 16)  # Smaller font for debug info
        debug_info = [
            f"Paused: {self.paused}",
            f"Trick Completed: {self.trick_completed}",
            f"Auto Play: {self.auto_play}",
        ]

        for i, info in enumerate(debug_info):
            debug_text = debug_font.render(info, True, WHITE)
            debug_rect = debug_text.get_rect()
            debug_rect.right = WINDOW_WIDTH - 10
            debug_rect.bottom = WINDOW_HEIGHT - (len(debug_info) - 1 - i) * 15
            self.screen.blit(debug_text, debug_rect)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            running = self.handle_events()
            self.update()
            self.draw()

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
