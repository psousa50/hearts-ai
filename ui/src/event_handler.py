from typing import Optional, Tuple

import pygame
from card_sprite import CARD_HEIGHT, CARD_WIDTH
from game_state import GameState
from layout_manager import LayoutManager


class EventHandler:
    def __init__(self, game_state: GameState, layout: LayoutManager):
        self.game_state = game_state
        self.layout = layout

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click events"""
        if not self.game_state.current_player_is_human:
            return True

        # Check if clicked on a card in the player's hand
        hand = self.game_state.hands[0]
        start_x, start_y = self.layout.hand_positions[0]["start"]
        offset_x, _ = self.layout.hand_positions[0]["offset"]

        # Check cards from right to left
        for i in range(len(hand) - 1, -1, -1):
            card = hand[i]
            x = start_x + (i * offset_x)
            rect = pygame.Rect(x, start_y, CARD_WIDTH, CARD_HEIGHT)

            if rect.collidepoint(pos):
                try:
                    return self._handle_card_play(card, (x, start_y))
                except ValueError:
                    return True  # Invalid move, but continue game
        return True

    def _handle_card_play(self, card, start_pos: Tuple[int, int]) -> bool:
        """Handle playing a card"""
        played_card = self.game_state.play_card(0, card)
        if played_card is not None:
            self.game_state.last_auto_play = pygame.time.get_ticks()
            return True
        return True

    def handle_key(self, key: int) -> bool:
        """Handle keyboard events"""
        if key == pygame.K_SPACE:
            if self.game_state.paused:
                self.game_state.paused = False
                self.game_state.trick_completed = False
                self.game_state.last_auto_play = pygame.time.get_ticks()
        elif key == pygame.K_RETURN:
            self.game_state.auto_play = not self.game_state.auto_play
        elif key == pygame.K_ESCAPE:
            return False
        return True

    def handle_events(self) -> bool:
        """Process all pending events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.handle_click(event.pos):
                    return False
            elif event.type == pygame.KEYDOWN:
                if not self.handle_key(event.key):
                    return False
        return True
