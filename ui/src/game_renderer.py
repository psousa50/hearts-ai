from typing import List

import pygame
from animation_manager import AnimationManager
from card_sprite import CARD_HEIGHT, CARD_WIDTH, CardSprite
from game_state import GameState
from hearts_game_core.game_core import HeartsGame
from hearts_game_core.game_models import Card
from layout_manager import LayoutManager


class GameRenderer:
    # Colors
    WHITE = (255, 255, 255)
    GREEN = (34, 139, 34)
    RED = (255, 0, 0)
    BLACK = (0, 0, 0)
    DARK_GREEN = (0, 100, 0)
    YELLOW = (255, 255, 0)

    def __init__(self, screen: pygame.Surface, layout: LayoutManager):
        self.screen = screen
        self.layout = layout
        self.font = pygame.font.Font(None, 36)
        self.medium_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 16)

    def draw_player_hand(
        self, player_idx: int, hand: List[Card], valid_moves: List[Card] = None, highlight_valid_moves: bool = False
    ):
        """Draw a player's hand with optional highlighting of valid moves"""
        for i, card in enumerate(hand):
            sprite = CardSprite(card)
            x, y = self.layout.get_hand_position(player_idx, i)

            if valid_moves and card in valid_moves and highlight_valid_moves:
                pygame.draw.rect(
                    self.screen,
                    self.YELLOW,
                    (x - 3, y - 3, CARD_WIDTH + 6, CARD_HEIGHT + 6),
                )

            self.screen.blit(sprite.image, (x, y))

    def draw_player_info(
        self, player_idx: int, name: str, strategy_name: str, score: int
    ):
        """Draw player information including name, strategy, and score"""
        pos = self.layout.get_player_info_position(player_idx)

        name_surface = self.font.render(name, True, self.WHITE)
        strategy_surface = self.medium_font.render(
            f"({strategy_name})", True, self.WHITE
        )
        score_surface = self.font.render(str(score), True, self.WHITE)

        name_rect = name_surface.get_rect(center=(pos[0], pos[1] - 15))
        strategy_rect = strategy_surface.get_rect(center=(pos[0], pos[1] + 5))
        score_rect = score_surface.get_rect(center=(pos[0], pos[1] + 30))

        # Background rectangle
        bg_rect = pygame.Rect(
            0,
            0,
            max(name_rect.width, strategy_rect.width, score_rect.width) + 20,
            name_rect.height + strategy_rect.height + score_rect.height + 25,
        )
        bg_rect.center = (pos[0], pos[1] + 5)

        pygame.draw.rect(self.screen, self.DARK_GREEN, bg_rect)
        self.screen.blit(name_surface, name_rect)
        self.screen.blit(strategy_surface, strategy_rect)
        self.screen.blit(score_surface, score_rect)

    def draw_game_info(self, current_player_name: str, trick_size: int):
        """Draw game status information"""
        game_info = f"Current Player: {current_player_name}"

        info_text = self.font.render(game_info, True, self.WHITE)
        self.screen.blit(info_text, (10, 10))

    def draw_cards_in_play(self, cards: List[CardSprite]):
        """Draw cards currently in play"""
        for card in cards:
            color = (
                None
                if card.good_move is None
                else self.DARK_GREEN
                if card.good_move
                else self.RED
            )
            if color:
                pygame.draw.rect(
                    self.screen,
                    color,
                    (card.rect.x - 3, card.rect.y - 3, CARD_WIDTH + 6, CARD_HEIGHT + 6),
                )

            self.screen.blit(card.image, card.rect)

    def render_frame(
        self, game_state: GameState, animation_mgr: AnimationManager
    ):
        """Render a complete frame"""
        # Clear screen
        self.screen.fill(self.GREEN)

        # Draw a circle at the trick center
        pygame.draw.circle(self.screen, self.WHITE, self.layout.trick_center, 10)

        # Draw player hands and info
        for i in range(4):
            valid_moves = (
                game_state.game.get_valid_moves(i) if game_state.current_player_is_human else None
            )
            hands = [p.hand for p in game_state.game.players]
            self.draw_player_hand(i, hands[i], valid_moves, highlight_valid_moves=i == game_state.game.current_player_index)
            self.draw_player_info(
                i,
                game_state.game.players[i].name,
                game_state.game.players[i].strategy.__class__.__name__,
                game_state.game.players[i].score
            )

        # Draw cards in play
        self.draw_cards_in_play(animation_mgr.get_cards_in_play())

        # Draw UI elements
        self.draw_game_info(game_state.game.current_player.name, game_state.game.current_trick.size)

        # Update display
        pygame.display.flip()
