import pygame
import json
import sys
import os
import io
from pathlib import Path
from typing import List, Dict, Tuple
from cairosvg import svg2png

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
CARD_WIDTH = 71
CARD_HEIGHT = 96
FPS = 60
ANIMATION_SPEED = 20
AUTO_PLAY_DELAY = 500  # milliseconds

# Colors
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)
DARK_GREEN = (0, 100, 0)  # Background color for player info

class Card:
    # Class-level cache for card images
    image_cache = {}

    def __init__(self, suit: str, rank: int):
        self.suit = suit
        self.rank = rank
        self.image = None
        self.rect = None
        self.target_pos = None
        self.current_pos = None
        self.moving = False
        self.load_image()

    def load_image(self):
        # Use numeric rank for all cards (no conversion needed)
        rank_str = str(self.rank)
        card_key = f"{rank_str}{self.suit}"
        
        # Check if image is already in cache
        if card_key in Card.image_cache:
            self.image = Card.image_cache[card_key]
        else:
            # Load SVG card image from assets folder using numeric format
            image_path = Path(__file__).parent / 'assets' / 'cards' / f'{card_key}.svg'
            if not image_path.exists():
                # Create a default card representation if image doesn't exist
                surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
                surf.fill(WHITE)
                pygame.draw.rect(surf, BLACK, (0, 0, CARD_WIDTH, CARD_HEIGHT), 2)
                font = pygame.font.Font(None, 36)
                text = font.render(card_key, True, BLACK)
                surf.blit(text, (10, 30))
                self.image = surf
            else:
                # Convert SVG to PNG in memory
                png_data = svg2png(url=str(image_path), output_width=CARD_WIDTH, output_height=CARD_HEIGHT)
                # Load PNG data into pygame surface
                png_file = io.BytesIO(png_data)
                self.image = pygame.image.load(png_file)
            
            # Cache the loaded image
            Card.image_cache[card_key] = self.image
        
        self.rect = self.image.get_rect()

    def move_towards_target(self):
        if not self.moving or not self.target_pos:
            return
        
        dx = self.target_pos[0] - self.current_pos[0]
        dy = self.target_pos[1] - self.current_pos[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        if distance < ANIMATION_SPEED:
            self.current_pos = self.target_pos
            self.moving = False
            return
        
        move_x = (dx / distance) * ANIMATION_SPEED
        move_y = (dy / distance) * ANIMATION_SPEED
        
        self.current_pos = (self.current_pos[0] + move_x, self.current_pos[1] + move_y)
        self.rect.center = self.current_pos

class GameVisualizer:
    def __init__(self, game_file: str):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hearts Game Visualizer")
        self.clock = pygame.time.Clock()
        
        # Load game data
        with open(game_file, 'r') as f:
            self.games = json.load(f)
        
        self.current_game = 0
        self.current_trick = 0
        self.current_card = 0
        
        # Player positions (center points for names and scores)
        self.player_positions = {
            0: (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50),   # Bottom
            1: (200, WINDOW_HEIGHT // 2),                 # Left
            2: (WINDOW_WIDTH // 2, 30),                   # Top
            3: (WINDOW_WIDTH - 200, WINDOW_HEIGHT // 2)   # Right
        }
        
        # Hand display positions and offsets (reduced spacing between cards)
        card_overlap = 30  # Only show 20 pixels of each card except the last
        self.hand_positions = {
            0: {"start": (WINDOW_WIDTH // 4, WINDOW_HEIGHT - 180),  # Bottom (above names)
                "offset": (card_overlap, 0)},
            1: {"start": (50, WINDOW_HEIGHT // 4),                  # Left (left of names)
                "offset": (0, card_overlap)},
            2: {"start": (WINDOW_WIDTH // 4, 70),                   # Top (below names)
                "offset": (card_overlap, 0)},
            3: {"start": (WINDOW_WIDTH - 120, WINDOW_HEIGHT // 4),  # Right (right of names)
                "offset": (0, card_overlap)}
        }
        
        self.cards_in_play: List[Card] = []
        self.trick_center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        
        # Initialize player info
        self.players = self.games[self.current_game]["players"]
        self.auto_play = False
        self.last_auto_play = pygame.time.get_ticks()

    def calculate_running_scores(self):
        scores = [0] * len(self.players)
        # Only count completed tricks
        for trick_idx in range(self.current_trick):
            trick = self.games[self.current_game]["tricks"][trick_idx]
            winner = trick["winner"]
            scores[winner] += trick["points"]
        
        # Add current trick points only if all cards have been played
        if self.current_trick < len(self.games[self.current_game]["tricks"]):
            current_trick = self.games[self.current_game]["tricks"][self.current_trick]
            if self.current_card == len(current_trick["cards"]):
                scores[current_trick["winner"]] += current_trick["points"]
        
        return scores

    def get_current_trick(self):
        return self.games[self.current_game]["tricks"][self.current_trick]
    
    def get_total_tricks(self):
        return len(self.games[self.current_game]["tricks"])

    def create_card_for_play(self, card_data: Dict, player_idx: int):
        card = Card(card_data["suit"], card_data["rank"])
        start_pos = self.player_positions[player_idx]
        
        # Calculate target position in a diamond pattern
        # Offset from center based on player position
        offsets = {
            0: (0, 60),      # Bottom player's card goes below center
            1: (-60, 0),     # Left player's card goes left of center
            2: (0, -60),     # Top player's card goes above center
            3: (60, 0)       # Right player's card goes right of center
        }
        offset_x, offset_y = offsets[player_idx]
        target_pos = (
            self.trick_center[0] + offset_x,
            self.trick_center[1] + offset_y
        )
        
        card.current_pos = start_pos
        card.target_pos = target_pos
        card.rect.center = start_pos
        card.moving = True
        return card

    def next_card(self):
        trick = self.get_current_trick()
        if self.current_card < len(trick["cards"]):
            # Add next card to current trick
            card_data = trick["cards"][self.current_card]
            card = self.create_card_for_play(card_data["card"], card_data["player_index"])
            self.cards_in_play.append(card)
            self.current_card += 1
            return True
        elif self.current_trick < self.get_total_tricks() - 1:
            # Move to next trick
            self.current_trick += 1
            self.current_card = 0
            self.cards_in_play.clear()
            return True
        return False

    def previous_trick(self):
        if self.current_trick > 0:
            self.current_trick -= 1
            self.current_card = 0
            self.cards_in_play.clear()

    def next_trick(self):
        if self.current_trick < len(self.games[self.current_game]["tricks"]) - 1:
            self.current_trick += 1
            self.current_card = 0
            self.cards_in_play.clear()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if event.key == pygame.K_SPACE:
                    self.auto_play = not self.auto_play
                elif event.key == pygame.K_LEFT:
                    if mods & pygame.KMOD_SHIFT:
                        # Previous trick
                        if self.current_trick > 0:
                            self.current_trick -= 1
                            self.current_card = 0
                            self.cards_in_play.clear()
                    else:
                        # Previous card
                        if self.current_card > 0:
                            self.current_card -= 1
                            self.cards_in_play.pop()
                elif event.key == pygame.K_RIGHT:
                    if mods & pygame.KMOD_SHIFT:
                        self.next_trick()
                    else:
                        # Next card or next trick if at end of current trick
                        trick = self.get_current_trick()
                        if self.current_card < len(trick["cards"]):
                            self.next_card()
                        elif self.current_trick < len(self.games[self.current_game]["tricks"]) - 1:
                            self.next_trick()
        return True

    def draw_player_hand(self, player_idx: int, hand: List[Dict]):
        pos = self.hand_positions[player_idx]
        start_x, start_y = pos["start"]
        offset_x, offset_y = pos["offset"]
        
        for i, card_data in enumerate(hand):
            card = Card(card_data["suit"], card_data["rank"])
            x = start_x + (i * offset_x)
            y = start_y + (i * offset_y)
            self.screen.blit(card.image, (x, y))

    def draw(self):
        # Draw background
        self.screen.fill(GREEN)
        
        # Draw player positions and scores
        font = pygame.font.Font(None, 36)
        running_scores = self.calculate_running_scores()
        
        for player in self.players:
            pos = self.player_positions[player["index"]]
            
            # Create background rectangle for player info
            text = f"{player['name']} ({player['strategy']})"
            text_surface = font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=(pos[0], pos[1]))
            bg_rect = text_rect.inflate(20, 10)  # Make background slightly larger
            
            score_text = str(running_scores[player["index"]])
            score_surface = font.render(score_text, True, WHITE)
            score_rect = score_surface.get_rect(center=(pos[0], pos[1] + 30))
            score_bg_rect = score_rect.inflate(20, 10)
            
            # Draw background rectangles
            pygame.draw.rect(self.screen, DARK_GREEN, bg_rect)
            pygame.draw.rect(self.screen, DARK_GREEN, score_bg_rect)
            
            # Draw text
            self.screen.blit(text_surface, text_rect)
            self.screen.blit(score_surface, score_rect)
        
        # Draw current hands for all players
        trick = self.get_current_trick()
        if self.current_card < len(trick["cards"]):
            # Show all player hands from the current state
            for player_idx in range(4):
                # Find the most recent hand state for this player
                hand = None
                for i in range(self.current_card, -1, -1):
                    if trick["cards"][i]["player_index"] == player_idx:
                        hand = trick["cards"][i]["hand"]
                        break
                if hand:
                    self.draw_player_hand(player_idx, hand)
        
        # Draw cards in play
        for card in self.cards_in_play:
            card.move_towards_target()
            self.screen.blit(card.image, card.rect)
        
        # Draw game info and current trick score
        trick = self.get_current_trick()
        game_info = f"Game {self.current_game + 1} - Trick {self.current_trick + 1}/{self.get_total_tricks()} - Card {self.current_card}/{len(trick['cards'])}"
        info_text = font.render(game_info, True, WHITE)
        self.screen.blit(info_text, (10, 10))
        
        # Draw current trick info if all cards are played
        if self.current_card == len(trick["cards"]):
            winner = self.players[trick["winner"]]["name"]
            trick_info = f"Trick winner: {winner} (+{trick['points']} points)"
            trick_text = font.render(trick_info, True, WHITE)
            self.screen.blit(trick_text, (10, 40))
        
        # Draw controls info
        controls = [
            "Controls:",
            "Space - Toggle auto-play",
            "Left/Right - Previous/Next card",
            "Shift+Left/Right - Previous/Next trick",
            "Close window to quit"
        ]
        small_font = pygame.font.Font(None, 24)  # Smaller font for controls
        for i, control in enumerate(controls):
            control_text = small_font.render(control, True, WHITE)
            self.screen.blit(control_text, (10, WINDOW_HEIGHT - 20 * (len(controls) - i)))
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            
            running = self.handle_events()
            
            # Handle auto-play
            if self.auto_play:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_auto_play > AUTO_PLAY_DELAY:
                    self.next_card()
                    self.last_auto_play = current_time
            
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python game_visualizer.py <game_file.json>")
        sys.exit(1)
    
    game_file = sys.argv[1]
    if not os.path.exists(game_file):
        print(f"Error: File {game_file} not found")
        sys.exit(1)
    
    visualizer = GameVisualizer(game_file)
    visualizer.run()
