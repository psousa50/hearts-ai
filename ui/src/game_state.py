from typing import List, Optional, Tuple

import pygame
from hearts_game import Card, HeartsGame, Player
from strategies import HumanStrategy


class GameState:
    def __init__(self, game: HeartsGame):
        self.game = game
        self.current_trick = 0
        self.current_card = 0
        self.auto_play = False
        self.last_auto_play = pygame.time.get_ticks()
        self.selected_card = None
        self.trick_completed = False
        self.trick_completion_time = 0
        self.paused = False

    def reset_game(self):
        self.game.reset_game()
        self.current_trick = 0
        self.current_card = 0
        self.auto_play = False
        self.selected_card = None
        self.trick_completed = False
        self.trick_completion_time = 0
        self.paused = False
