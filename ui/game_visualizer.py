import pygame
import json
import sys
import os
import io
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from hearts_game import HeartsGame, Card, RandomStrategy, AvoidPointsStrategy, AggressiveStrategy, AIStrategy
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
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)

class CardSprite:
    # Class-level cache for card images
    image_cache = {}

    def __init__(self, card: Card):
        self.card = card
        self.image = None
        self.rect = None
        self.target_pos = None
        self.current_pos = None
        self.moving = False
        self.load_image()

    def load_image(self):
        # Use numeric rank for all cards (no conversion needed)
        card_key = f"{self.card.rank}{self.card.suit}"
        
        # Check if image is already in cache
        if card_key in CardSprite.image_cache:
            self.image = CardSprite.image_cache[card_key]
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
            CardSprite.image_cache[card_key] = self.image
        
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
    def __init__(self, game_file: Optional[str] = None):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hearts Game Visualizer")
        self.clock = pygame.time.Clock()
        
        # Player positions (center points for names and scores)
        self.player_positions = {
            0: (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50),   # Bottom (moved up a bit)
            1: (200, WINDOW_HEIGHT // 2),                 # Left
            2: (WINDOW_WIDTH // 2, 30),                   # Top
            3: (WINDOW_WIDTH - 200, WINDOW_HEIGHT // 2)   # Right
        }
        
        # Hand display positions and offsets (reduced spacing between cards)
        card_overlap = 20  # Only show 20 pixels of each card except the last
        self.hand_positions = {
            0: {"start": (WINDOW_WIDTH // 4, WINDOW_HEIGHT - 200),  # Bottom
                "offset": (card_overlap, 0)},
            1: {"start": (50, WINDOW_HEIGHT // 4),                  # Left
                "offset": (0, card_overlap)},
            2: {"start": (WINDOW_WIDTH // 4, 70),                   # Top
                "offset": (card_overlap, 0)},
            3: {"start": (WINDOW_WIDTH - 120, WINDOW_HEIGHT // 4),  # Right
                "offset": (0, card_overlap)}
        }
        
        self.cards_in_play: List[CardSprite] = []
        self.trick_center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        
        if game_file:
            # Load game from file
            with open(game_file, 'r') as f:
                self.games = json.load(f)
            self.current_game = 0
            self.current_trick = 0
            self.current_card = 0
            self.game = None
            self.replay_mode = True
        else:
            # Create new real-time game
            self.games = None
            self.current_game = 0
            self.current_trick = 0
            self.current_card = 0
            self.game = HeartsGame([
                ("You", RandomStrategy()),  # Bottom player (human)
                ("Bob", AvoidPointsStrategy()),  # Left player
                ("Charlie", AggressiveStrategy()),  # Top player
                ("AI", AIStrategy())  # Right player
            ])
            self.replay_mode = False
        
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
            self.trick_completed = True
            self.paused = True
            self.game.complete_trick()
            return True
        return False

    def handle_click(self, pos):
        if not self.replay_mode and self.game.current_player == 0:
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
                        sprite = CardSprite(played_card)
                        sprite.current_pos = (x + CARD_WIDTH//2, start_y + CARD_HEIGHT//2)
                        sprite.target_pos = self.get_trick_position(len(self.game.current_trick) - 1)
                        sprite.moving = True
                        self.cards_in_play.append(sprite)
                        self.last_auto_play = pygame.time.get_ticks()
                        
                        # Check if trick is complete after human plays
                        if not any(card.moving for card in self.cards_in_play):
                            self.check_and_complete_trick()
                        
                        # Update AI state with played card
                        for _, strategy in self.game.players:
                            if isinstance(strategy, AIStrategy):
                                strategy.current_trick_cards = [(c.suit, c.rank) for c, _ in self.game.current_trick]
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
                    self.auto_play = not self.auto_play  # Toggle auto-play if not paused
                elif event.key == pygame.K_ESCAPE:
                    return False
                mods = pygame.key.get_mods()
                if self.replay_mode:
                    if event.key == pygame.K_LEFT:
                        if mods & pygame.KMOD_SHIFT:
                            if self.current_trick > 0:
                                self.current_trick -= 1
                                self.current_card = 0
                                self.clear_trick_cards()
                        else:
                            if self.current_card > 0:
                                self.current_card -= 1
                                self.cards_in_play.pop()
                    elif event.key == pygame.K_RIGHT:
                        if mods & pygame.KMOD_SHIFT:
                            self.next_trick()
                        else:
                            trick = self.get_current_trick()
                            if self.current_card < len(trick["cards"]):
                                self.next_card()
                            elif self.current_trick < len(self.games[self.current_game]["tricks"]) - 1:
                                self.next_trick()
        return True

    def update(self):
        print("pausing", self.paused)
        print("trick completed", self.trick_completed)
        print("auto play", self.auto_play)
        print("replay mode", self.replay_mode)
        if not self.replay_mode:
            current_time = pygame.time.get_ticks()
            
            # Don't update if paused
            if self.paused:
                return
            
            # Only auto-play for AI players or if auto_play is explicitly enabled
            if self.game.current_player != 0 or (self.auto_play and self.game.current_player == 0):
                if current_time - self.last_auto_play > AUTO_PLAY_DELAY:
                    # Wait for any card animations to finish before checking trick completion
                    if any(card.moving for card in self.cards_in_play):
                        return
                        
                    # Check if trick is complete
                    if self.check_and_complete_trick():
                        return
                    
                    # If this is the start of a new trick, clear any remaining cards
                    if len(self.game.current_trick) == 0:
                        self.clear_trick_cards()
                    
                    # Play next card
                    card = self.game.play_card(self.game.current_player)
                    start_pos = self.hand_positions[self.game.current_player]["start"]
                    sprite = CardSprite(card)
                    sprite.current_pos = (start_pos[0] + CARD_WIDTH//2, 
                                        start_pos[1] + CARD_HEIGHT//2)
                    sprite.target_pos = self.get_trick_position(len(self.game.current_trick) - 1)
                    sprite.moving = True
                    self.cards_in_play.append(sprite)
                    
                    # Check if trick is complete after AI plays
                    if not any(card.moving for card in self.cards_in_play):
                        self.check_and_complete_trick()
                    
                    # Update AI state with played card
                    for _, strategy in self.game.players:
                        if isinstance(strategy, AIStrategy):
                            strategy.current_trick_cards = [(c.suit, c.rank) for c, _ in self.game.current_trick]
                    self.last_auto_play = current_time

            # Check for game over
            if self.game.get_game_state()["game_over"]:
                # Start a new game after a delay
                if current_time - self.last_auto_play > AUTO_PLAY_DELAY * 2:
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
                    self.last_auto_play = current_time

        # Update card animations
        moving_cards = []
        for card in self.cards_in_play:
            if card.moving:
                card.move_towards_target()
                moving_cards.append(card)
            elif not self.trick_completed:  # Only keep non-moving cards if trick is not completed
                moving_cards.append(card)
        self.cards_in_play = moving_cards

    def get_trick_position(self, card_index: int) -> Tuple[int, int]:
        # Position cards in a diamond pattern around the center
        offsets = [
            (0, 60),      # Bottom player's card goes below center
            (-60, 0),     # Left player's card goes left of center
            (0, -60),     # Top player's card goes above center
            (60, 0)       # Right player's card goes right of center
        ]
        offset_x, offset_y = offsets[card_index]
        return (self.trick_center[0] + offset_x,
                self.trick_center[1] + offset_y)

    def draw_player_hand(self, player_idx: int, hand: List[Card], highlight_valid: bool = False):
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
                pygame.draw.rect(self.screen, (255, 255, 0), 
                               (x-2, y-2, CARD_WIDTH+4, CARD_HEIGHT+4))
            
            self.screen.blit(sprite.image, (x, y))

    def draw(self):
        self.screen.fill(GREEN)
        
        # Get current game state
        if self.replay_mode:
            game_state = self.games[self.current_game]
            trick = self.get_current_trick()
            current_trick = trick["cards"][:self.current_card + 1] if trick else []
            current_player = (len(current_trick)) % 4 if current_trick else 0
            hands = game_state["hands"]
            scores = game_state["scores"]
            players = game_state["players"]
        else:
            game_state = self.game.get_game_state()
            current_trick = game_state["current_trick"]
            current_player = game_state["current_player"]
            hands = game_state["hands"]
            scores = game_state["scores"]
            players = game_state["players"]
        
        # Draw player positions and scores
        font = pygame.font.Font(None, 36)
        medium_font = pygame.font.Font(None, 24)
        
        for i, player in enumerate(players):
            pos = self.player_positions[i]
            
            # Create background rectangle for player info
            name_text = player['name']
            strategy_text = f"({player['strategy']})"
            score_text = str(scores[i])
            
            name_surface = font.render(name_text, True, WHITE)
            strategy_surface = medium_font.render(strategy_text, True, WHITE)
            score_surface = font.render(score_text, True, WHITE)
            
            name_rect = name_surface.get_rect(center=(pos[0], pos[1] - 15))
            strategy_rect = strategy_surface.get_rect(center=(pos[0], pos[1] + 5))
            score_rect = score_surface.get_rect(center=(pos[0], pos[1] + 30))
            
            # Calculate background rectangle to fit all elements
            bg_rect = pygame.Rect(0, 0, 
                                max(name_rect.width, strategy_rect.width, score_rect.width) + 20, 
                                name_rect.height + strategy_rect.height + score_rect.height + 25)
            bg_rect.center = (pos[0], pos[1] + 5)
            
            pygame.draw.rect(self.screen, DARK_GREEN, bg_rect)
            self.screen.blit(name_surface, name_rect)
            self.screen.blit(strategy_surface, strategy_rect)
            self.screen.blit(score_surface, score_rect)

        # Draw pause overlay
        if self.paused:
            # Calculate trick points
            trick_points = 0
            for card, _ in current_trick:
                if card.suit == 'H':
                    trick_points += 1
                elif card.suit == 'S' and card.rank == 12:  # Queen of Spades
                    trick_points += 13

            # Draw pause info box
            info_lines = [
                ("Press SPACE to continue", WHITE),
                (f"Trick Points: {trick_points}", RED if trick_points > 0 else WHITE)
            ]
            
            line_height = 30
            total_height = line_height * len(info_lines)
            y_start = WINDOW_HEIGHT // 2 + 80
            
            for i, (text, color) in enumerate(info_lines):
                text_surface = font.render(text, True, color)
                text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, y_start + i * line_height))
                bg_rect = text_rect.inflate(20, 10)
                pygame.draw.rect(self.screen, BLACK, bg_rect)
                self.screen.blit(text_surface, text_rect)
        
        # Draw hands
        if self.replay_mode:
            if self.current_card < len(trick["cards"]):
                current_hand = trick["cards"][self.current_card]["hand"]
                for player_idx in range(4):
                    if player_idx == trick["cards"][self.current_card]["player_index"]:
                        self.draw_player_hand(player_idx, current_hand)
                    elif self.current_card > 0:
                        prev_hand = trick["cards"][self.current_card - 1]["hand"]
                        if trick["cards"][self.current_card - 1]["player_index"] == player_idx:
                            self.draw_player_hand(player_idx, prev_hand)
        else:
            # Draw current hands for all players
            for i in range(4):
                self.draw_player_hand(i, self.game.hands[i], 
                                    i == 0 and self.game.current_player == 0)
        
        # Draw cards in play
        for card in self.cards_in_play:
            card.move_towards_target()
            self.screen.blit(card.image, card.rect)
        
        # Draw game info
        if self.replay_mode:
            game_info = f"Game {self.current_game + 1} - Trick {self.current_trick + 1}/{len(game_state['tricks'])} - Card {self.current_card}/{len(trick['cards'])}"
        else:
            game_info = f"Current Player: {players[self.game.current_player]['name']}"
            if len(self.game.current_trick) > 0:
                game_info += f" - Cards in trick: {len(self.game.current_trick)}/4"
        
        info_text = font.render(game_info, True, WHITE)
        self.screen.blit(info_text, (10, 10))
        
        # Draw controls info
        controls = [
            "Controls:",
            "Space - Toggle auto-play",
        ]
        if self.replay_mode:
            controls.extend([
                "Left/Right - Previous/Next card",
                "Shift+Left/Right - Previous/Next trick",
            ])
        else:
            controls.append("Click card to play (when it's your turn)")
        controls.append("Close window to quit")
        
        small_font = pygame.font.Font(None, 24)
        for i, control in enumerate(controls):
            control_text = small_font.render(control, True, WHITE)
            self.screen.blit(control_text, (10, WINDOW_HEIGHT - 20 * (len(controls) - i)))
        
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
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Replay mode: python game_visualizer.py <game_file.json>")
        print("  Real-time mode: python game_visualizer.py --realtime")
        sys.exit(1)
    
    if sys.argv[1] == "--realtime":
        visualizer = GameVisualizer()
    else:
        game_file = sys.argv[1]
        if not os.path.exists(game_file):
            print(f"Error: File {game_file} not found")
            sys.exit(1)
        visualizer = GameVisualizer(game_file)
    
    visualizer.run()
