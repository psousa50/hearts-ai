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

    @property
    def current_player_is_human(self) -> bool:
        return isinstance(self.current_player.strategy, HumanStrategy)

    @property
    def current_player(self) -> Player:
        return self.game.players[self.game.current_player_index]

    @property
    def current_player_index(self) -> int:
        return self.game.current_player_index

    @property
    def hands(self) -> List[List[Card]]:
        return self.game.hands

    @property
    def scores(self) -> List[int]:
        return self.game.scores

    @property
    def players(self) -> List[Player]:
        return self.game.players

    @property
    def current_trick_cards(self) -> List[Tuple[Card, int]]:
        return self.game.current_trick

    def get_valid_moves(self, player_idx: int) -> List[Card]:
        return self.game.get_valid_moves(player_idx)

    def play_card(self, player_idx: int, card: Optional[Card] = None) -> Optional[Card]:
        return self.game.play_card(player_idx, card)

    def is_game_over(self) -> bool:
        return self.game.game_over()

    def reset_game(self):
        self.game.reset_game()
        self.current_trick = 0
        self.current_card = 0
        self.auto_play = False
        self.selected_card = None
        self.trick_completed = False
        self.trick_completion_time = 0
        self.paused = False
