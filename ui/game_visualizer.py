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

# Colors
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)

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
        
        # Player positions (center points for cards)
        self.player_positions = {
            0: (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100),  # Bottom
            1: (100, WINDOW_HEIGHT // 2),                 # Left
            2: (WINDOW_WIDTH // 2, 100),                 # Top
            3: (WINDOW_WIDTH - 100, WINDOW_HEIGHT // 2)   # Right
        }
        
        self.cards_in_play: List[Card] = []
        self.trick_center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        
        # Initialize player info
        self.players = self.games[self.current_game]["players"]

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
        if self.current_trick < self.get_total_tricks() - 1:
            self.current_trick += 1
            self.current_card = 0
            self.cards_in_play.clear()

    def draw(self):
        # Draw background
        self.screen.fill(GREEN)
        
        # Draw player positions and scores
        font = pygame.font.Font(None, 36)
        running_scores = self.calculate_running_scores()
        
        for player in self.players:
            pos = self.player_positions[player["index"]]
            # Draw player name and strategy
            text = font.render(f"{player['name']} ({player['strategy']})", True, WHITE)
            text_rect = text.get_rect(center=(pos[0], pos[1] + (30 if player["index"] % 2 == 0 else 0)))
            self.screen.blit(text, text_rect)
            
            # Draw running score
            score_text = font.render(str(running_scores[player["index"]]), True, WHITE)
            score_rect = score_text.get_rect(center=(pos[0], pos[1] + (60 if player["index"] % 2 == 0 else 30)))
            self.screen.blit(score_text, score_rect)
        
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
            "N - Play next card",
            "Left/Right Arrow - Previous/Next trick",
            "Close window to quit"
        ]
        for i, control in enumerate(controls):
            control_text = font.render(control, True, WHITE)
            self.screen.blit(control_text, (10, WINDOW_HEIGHT - 30 * (len(controls) - i)))
        
        pygame.display.flip()

    def run(self):
        running = True
        auto_play = False
        delay = 0
        
        while running:
            self.clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        auto_play = not auto_play
                    elif event.key == pygame.K_LEFT:
                        self.previous_trick()
                    elif event.key == pygame.K_RIGHT:
                        self.next_trick()
                    elif event.key == pygame.K_n:
                        self.next_card()
            
            # Handle auto-play
            if auto_play:
                delay += 1
                if delay >= FPS // 2:  # Play a card every half second
                    if not self.next_card():
                        auto_play = False
                    delay = 0
            
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
