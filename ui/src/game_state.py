import pygame

from hearts_game_core.game_core import HeartsGame
from strategies.human import HumanStrategy


class GameState:
    def __init__(self, game: HeartsGame):
        self.game = game
        self.reset_game()

    def reset_game(self):
        self.game.reset_game()
        self.paused = False
        self.last_auto_play = pygame.time.get_ticks()

    @property
    def current_player_is_human(self) -> bool:
        return isinstance(self.game.current_player.strategy, HumanStrategy)
