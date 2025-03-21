from typing import List, Tuple

from card_sprite import CardSprite


class AnimationManager:
    def __init__(self):
        self.cards_in_play: List[CardSprite] = []

    def add_card_animation(
        self,
        card_sprite: CardSprite,
        start_pos: Tuple[int, int],
        target_pos: Tuple[int, int],
    ):
        card_sprite.current_pos = start_pos
        card_sprite.rect.topleft = start_pos
        card_sprite.target_pos = target_pos
        card_sprite.moving = True
        self.cards_in_play.append(card_sprite)

    def update_animations(self):
        """Update all card animations and return list of cards still in play"""
        for card in self.cards_in_play:
            if card.moving:
                card.move_towards_target()

    def clear_animations(self):
        """Clear all card animations"""
        self.cards_in_play = []

    def has_moving_cards(self) -> bool:
        """Check if any cards are still animating"""
        return any(card.moving for card in self.cards_in_play)

    def get_cards_in_play(self) -> List[CardSprite]:
        return self.cards_in_play
