from typing import Callable, Tuple

import pygame
from game_renderer import CARD_HEIGHT, CARD_WIDTH
from game_state import GameState
from hearts_game_core.game_core import HeartsGame
from hearts_game_core.game_models import Card
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
        if not self.game_state.current_player_is_human:
            if self.game_state.paused:
                self.game_state.paused = False
            return

        player_idx = self.game.current_player_index
        hand = self.game.players[player_idx].hand

        valid_moves = self.game.get_valid_moves(player_idx)

        for i in range(len(hand) - 1, -1, -1):
            card = hand[i]
            x, y = self.layout.get_hand_position(player_idx, i)
            rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)

            if rect.collidepoint(pos):
                if card in valid_moves:
                    self.play_card_handler(card)
                return

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
