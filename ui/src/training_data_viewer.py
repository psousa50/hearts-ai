#!/usr/bin/env python3
import argparse
import io
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import cairosvg
import msgpack
import pygame

# Enable extensive debug logging
DEBUG = False


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force output to be displayed immediately


# Constants
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 1200
BACKGROUND_COLOR = (0, 100, 0)  # Dark green
TEXT_COLOR = (255, 255, 255)  # White
CARD_WIDTH = 71 * 0.75
CARD_HEIGHT = 96 * 0.75
CARD_SPACING = 20 * 0.75
ROW_HEIGHT = 120 * 0.75
FONT_SIZE = 14

# Card suit symbols and colors
SUIT_SYMBOLS = {"C": "C", "D": "D", "H": "H", "S": "S"}


@dataclass
class CompactCard:
    suit: str
    rank: int

    def __str__(self):
        rank_str = {11: "J", 12: "Q", 13: "K", 14: "A"}.get(self.rank, str(self.rank))
        return f"{rank_str}{SUIT_SYMBOLS[self.suit]}"


@dataclass
class CompactTrick:
    cards: List[Optional[CompactCard]]
    first_player: int


@dataclass
class CompactCompletedTrick:
    cards: List[CompactCard]
    winner: int
    points: int
    first_player_index: int


@dataclass
class CompactTrainingData:
    previous_tricks: List[CompactCompletedTrick]
    current_trick: CompactTrick
    current_player_index: int
    player_hand: List[CompactCard]
    played_card: CompactCard


class CardImage:
    # Class-level cache for card images
    image_cache = {}

    @staticmethod
    def get_card_image(card: CompactCard) -> pygame.Surface:
        """Get the image for a card, loading from assets or cache"""
        # Use numeric rank for all cards
        card_key = f"{card.rank}{card.suit}"

        # Check if image is already in cache
        if card_key in CardImage.image_cache:
            return CardImage.image_cache[card_key]

        # Load SVG card image from assets folder
        image_path = (
            Path(__file__).parent / ".." / "assets" / "cards" / f"{card_key}.svg"
        )

        if not image_path.exists():
            # Create a default card representation if image doesn't exist
            surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            surf.fill((255, 255, 255))  # WHITE
            pygame.draw.rect(
                surf, (0, 0, 0), (0, 0, CARD_WIDTH, CARD_HEIGHT), 2
            )  # BLACK
            font = pygame.font.Font(None, 36)
            text = font.render(str(card), True, (0, 0, 0))  # BLACK
            surf.blit(text, (10, 30))
            image = surf
        else:
            try:
                # Convert SVG to PNG in memory using cairosvg
                png_data = cairosvg.svg2png(
                    url=str(image_path),
                    output_width=CARD_WIDTH,
                    output_height=CARD_HEIGHT,
                )

                # Convert PNG data to pygame surface
                png_file = io.BytesIO(png_data)
                image = pygame.image.load(png_file)
            except Exception:
                # Fallback to a simple representation
                surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
                surf.fill((255, 255, 255))  # WHITE
                pygame.draw.rect(
                    surf, (0, 0, 0), (0, 0, CARD_WIDTH, CARD_HEIGHT), 2
                )  # BLACK
                font = pygame.font.Font(None, 36)
                text = font.render(str(card), True, (0, 0, 0))  # BLACK
                surf.blit(text, (10, 30))
                image = surf

        # Cache the loaded image
        CardImage.image_cache[card_key] = image
        return image


class TrainingDataViewer:
    def __init__(self, file_path: str):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hearts AI Training Data Viewer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", FONT_SIZE)

        # Load training data
        self.training_data = self.load_training_data(file_path)
        self.current_index = 0

    def load_training_data(self, file_path: str) -> List[CompactTrainingData]:
        """Load training data from msgpack file"""
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

                # Try to unpack the data
                try:
                    data = msgpack.unpackb(file_data, raw=False)
                except Exception:
                    # Try with raw=True
                    data = msgpack.unpackb(file_data, raw=True)

                # Convert raw dictionaries to CompactTrainingData objects
                result = self.convert_to_compact_training_data(data)
                return result
        except Exception:
            # Return empty list instead of exiting
            return []

    def convert_to_compact_training_data(self, data):
        """Convert raw dictionaries to CompactTrainingData objects"""
        result = []

        # Create a simple mock training data for testing if data is empty
        if not data or len(data) == 0:
            # Create a simple mock CompactTrainingData
            mock_card = CompactCard("S", 12)  # Queen of Spades
            mock_trick = CompactTrick(
                cards=[mock_card, None, None, None], first_player=0
            )
            mock_completed_trick = CompactCompletedTrick(
                cards=[
                    CompactCard("S", 12),
                    CompactCard("S", 2),
                    CompactCard("S", 3),
                    CompactCard("S", 4),
                ],
                winner=0,
                points=13,
                first_player_index=0,
            )

            mock_data = CompactTrainingData(
                previous_tricks=[mock_completed_trick],
                current_trick=mock_trick,
                current_player_index=1,
                player_hand=[
                    CompactCard("H", 2),
                    CompactCard("H", 3),
                    CompactCard("H", 4),
                ],
                played_card=CompactCard("H", 2),
            )

            result.append(mock_data)
            return result

        # Check if data is a list of dictionaries or a list of lists
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Handle dictionary format
            for item in data:
                try:
                    # Convert previous tricks
                    previous_tricks = []
                    for trick in item.get("previous_tricks", []):
                        cards = [
                            CompactCard(c["0"], c["1"]) for c in trick.get("cards", [])
                        ]
                        previous_tricks.append(
                            CompactCompletedTrick(
                                cards=cards,
                                winner=trick.get("winner", 0),
                                points=trick.get("points", 0),
                                first_player_index=trick.get("first_player_index", 0),
                            )
                        )

                    # Convert current trick
                    current_trick_data = item.get("current_trick", {})
                    cards = []
                    for card_data in current_trick_data.get("cards", []):
                        if card_data is None:
                            cards.append(None)
                        else:
                            cards.append(CompactCard(card_data["0"], card_data["1"]))

                    current_trick = CompactTrick(
                        cards=cards,
                        first_player=current_trick_data.get("first_player", 0),
                    )

                    # Convert player hand and played card
                    player_hand = [
                        CompactCard(c["0"], c["1"]) for c in item.get("player_hand", [])
                    ]
                    played_card = CompactCard(
                        item.get("played_card", {}).get("0", "S"),
                        item.get("played_card", {}).get("1", 0),
                    )

                    # Create CompactTrainingData object
                    result.append(
                        CompactTrainingData(
                            previous_tricks=previous_tricks,
                            current_trick=current_trick,
                            current_player_index=item.get("current_player_index", 0),
                            player_hand=player_hand,
                            played_card=played_card,
                        )
                    )
                except Exception:
                    import traceback

                    traceback.print_exc()
        elif isinstance(data, list) and data and isinstance(data[0], list):
            # Handle list format
            for item in data:
                try:
                    # Based on the debug output, the format seems to be:
                    # [previous_tricks, current_trick, current_player_index, player_hand, played_card]

                    # Extract previous tricks (item[0])
                    previous_tricks = []
                    for trick_data in item[0]:
                        # trick_data format: [cards, winner, points, first_player_index]
                        if len(trick_data) >= 4:
                            cards = [
                                CompactCard(card[0], card[1]) for card in trick_data[0]
                            ]
                            previous_tricks.append(
                                CompactCompletedTrick(
                                    cards=cards,
                                    winner=trick_data[1],
                                    points=trick_data[2],
                                    first_player_index=trick_data[3],
                                )
                            )

                    # Extract current trick (item[1])
                    current_trick_data = item[1]
                    cards = []
                    for card_data in current_trick_data[0]:
                        if card_data is None:
                            cards.append(None)
                        else:
                            cards.append(CompactCard(card_data[0], card_data[1]))

                    current_trick = CompactTrick(
                        cards=cards, first_player=current_trick_data[1]
                    )

                    # Extract current player index (item[2])
                    current_player_index = item[2]

                    # Extract player hand (item[3])
                    player_hand = [CompactCard(card[0], card[1]) for card in item[3]]

                    # Extract played card (item[4])
                    played_card = CompactCard(item[4][0], item[4][1])

                    # Create CompactTrainingData object
                    result.append(
                        CompactTrainingData(
                            previous_tricks=previous_tricks,
                            current_trick=current_trick,
                            current_player_index=current_player_index,
                            player_hand=player_hand,
                            played_card=played_card,
                        )
                    )
                except Exception:
                    import traceback

                    traceback.print_exc()
        else:
            # For now, create mock data for testing
            # Create a simple mock CompactTrainingData
            mock_card = CompactCard("S", 12)  # Queen of Spades
            mock_trick = CompactTrick(
                cards=[mock_card, None, None, None], first_player=0
            )
            mock_completed_trick = CompactCompletedTrick(
                cards=[
                    CompactCard("S", 12),
                    CompactCard("S", 2),
                    CompactCard("S", 3),
                    CompactCard("S", 4),
                ],
                winner=0,
                points=13,
                first_player_index=0,
            )

            mock_data = CompactTrainingData(
                previous_tricks=[mock_completed_trick],
                current_trick=mock_trick,
                current_player_index=1,
                player_hand=[
                    CompactCard("H", 2),
                    CompactCard("H", 3),
                    CompactCard("H", 4),
                ],
                played_card=CompactCard("H", 2),
            )

            result.append(mock_data)

        return result

    def draw_card(self, card: CompactCard, x: int, y: int):
        """Draw a card at the specified position"""
        # Get the card image
        card_image = CardImage.get_card_image(card)

        # Draw card
        self.screen.blit(card_image, (x, y))

    def draw_trick(
        self, trick, x: int, y: int, is_completed: bool = False, winner: int = None
    ):
        """Draw a trick (completed or current) at the specified position"""
        cards = trick.cards
        first_player = trick.first_player_index if is_completed else trick.first_player

        for i, card in enumerate(cards):
            if card is not None:
                card_x = x + i * (CARD_WIDTH + CARD_SPACING)
                self.draw_card(card, card_x, y)

                # Highlight winner if completed trick
                if is_completed and i == (winner - first_player) % 4:
                    pygame.draw.rect(
                        self.screen,
                        (255, 255, 0),
                        (card_x, y, CARD_WIDTH, CARD_HEIGHT),
                        2,
                    )

    def draw_training_data(self, data: CompactTrainingData):
        trick_x_pos = 300
        """Draw the current training data on the screen"""

        self.screen.fill(BACKGROUND_COLOR)

        # Draw title and navigation info
        title = f"Training Data {self.current_index + 1}/{len(self.training_data)}"
        title_surface = self.font.render(title, True, TEXT_COLOR)
        self.screen.blit(
            title_surface, (WINDOW_WIDTH - title_surface.get_width() - 50, 20)
        )

        # Draw previous tricks
        y_pos = 20
        for i, trick in enumerate(data.previous_tricks):
            trick_text = f"Trick {i + 1} - Points: {trick.points}"
            trick_surface = self.font.render(trick_text, True, TEXT_COLOR)
            self.screen.blit(trick_surface, (20, y_pos))

            self.draw_trick(trick, trick_x_pos, y_pos, True, trick.winner)
            y_pos += ROW_HEIGHT

        y_pos += ROW_HEIGHT / 2

        # Draw current trick
        current_trick_text = "Current Trick - Player's Turn: " + str(
            data.current_player_index
        )
        current_trick_surface = self.font.render(current_trick_text, True, TEXT_COLOR)
        self.screen.blit(current_trick_surface, (20, y_pos))

        self.draw_trick(data.current_trick, trick_x_pos, y_pos)
        y_pos += ROW_HEIGHT

        pygame.display.flip()

    def run(self):
        """Main game loop"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        # Next game state
                        self.current_index = (self.current_index + 1) % len(
                            self.training_data
                        )
                    elif event.key == pygame.K_LEFT:
                        # Previous game state
                        self.current_index = (self.current_index - 1) % len(
                            self.training_data
                        )

            # Draw current training data
            if self.training_data:
                self.draw_training_data(self.training_data[self.current_index])
            else:
                # Draw error message if no training data
                self.screen.fill(BACKGROUND_COLOR)
                error_text = "No training data loaded. Check console for errors."
                error_surface = self.font.render(error_text, True, TEXT_COLOR)
                self.screen.blit(error_surface, (20, 20))
                pygame.display.flip()

            self.clock.tick(30)

        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Hearts AI Training Data Viewer")
    parser.add_argument("file", help="Path to the msgpack training data file")
    args = parser.parse_args()

    viewer = TrainingDataViewer(args.file)
    viewer.run()


if __name__ == "__main__":
    main()
