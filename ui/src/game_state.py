import pygame
from hearts_game_core.game_core import HeartsGame
from strategies.strategies import HumanStrategy


class GameState:
    def __init__(self, game: HeartsGame):
        self.game = game
        self.reset_game()

    def reset_game(self):
        self.game.reset_game()
        self.current_trick = 0
        self.current_card = 0
        self.auto_play = False
        self.selected_card = None
        self.trick_completed = False
        self.trick_completion_time = 0
        self.paused = False
        self.last_auto_play = pygame.time.get_ticks()

    @property
    def current_player_is_human(self) -> bool:
        return isinstance(self.game.current_player.strategy, HumanStrategy)
