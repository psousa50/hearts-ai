import pygame
import io
from pathlib import Path
from hearts_game import Card
from cairosvg import svg2png

# Constants
CARD_WIDTH = 71
CARD_HEIGHT = 96
ANIMATION_SPEED = 20

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

    def __str__(self):
        return f"{self.card}"

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
                surf.fill((255, 255, 255))  # WHITE
                pygame.draw.rect(surf, (0, 0, 0), (0, 0, CARD_WIDTH, CARD_HEIGHT), 2)  # BLACK
                font = pygame.font.Font(None, 36)
                text = font.render(card_key, True, (0, 0, 0))  # BLACK
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
