from typing import Callable, Optional, Tuple

import pygame
from card import Card
from card_sprite import CARD_HEIGHT, CARD_WIDTH
from game_state import GameState
from hearts_game import HeartsGame
from layout_manager import LayoutManager


class EventHandler:
    def __init__(
        self,
        game_state: GameState,
        game: HeartsGame,
        layout: LayoutManager,
        play_card_handler: Callable[[Card], None],
    ):
        self.game_state = game_state
        self.game = game
        self.layout = layout
        self.play_card_handler = play_card_handler

    def handle_click(self, pos: Tuple[int, int]):
        if not self.game.current_player_is_human:
            return

        # Check if clicked on a card in the player's hand
        hand = self.game.hands[self.game.current_player_index]
        start_x, start_y = self.layout.hand_positions[0]["start"]
        offset_x, _ = self.layout.hand_positions[0]["offset"]

        valid_moves = self.game.get_valid_moves(self.game.current_player_index)

        # Check cards from right to left
        for i in range(len(hand) - 1, -1, -1):
            card = hand[i]
            x = start_x + (i * offset_x)
            rect = pygame.Rect(x, start_y, CARD_WIDTH, CARD_HEIGHT)

            if rect.collidepoint(pos):
                print(f"Clicked on card {card}")
                print(f"Valid moves: {valid_moves}")
                if card in valid_moves:
                    self.play_card_handler(card)
                else:
                    break

    def handle_key(self, key: int) -> bool:
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                return self.handle_key(event.key)
        return True
