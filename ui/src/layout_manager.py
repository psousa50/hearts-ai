from typing import Tuple

from card_sprite import CARD_HEIGHT, CARD_WIDTH


class LayoutManager:
    def __init__(self, window_width: int, window_height: int):
        self.window_width = window_width
        self.window_height = window_height

        # Player positions (center points for names and scores)
        self.player_positions = {
            0: (window_width // 2, window_height - 50),  # Bottom
            1: (50, window_height // 2),  # Left
            2: (window_width // 2, 30),  # Top
            3: (window_width - 150, window_height // 2),  # Right
        }

        # Hand display positions and offsets
        card_overlap = 30
        self.hand_positions = {
            0: {
                "start": (window_width // 4, window_height - 200),  # Bottom
                "offset": (card_overlap, 0),
            },
            1: {
                "start": (150, window_height // 4),  # Left
                "offset": (0, card_overlap),
            },
            2: {
                "start": (window_width // 4, 90),  # Top
                "offset": (card_overlap, 0),
            },
            3: {
                "start": (window_width - 320, window_height // 4),  # Right
                "offset": (0, card_overlap),
            },
        }

        left_hand_right_edge = self.hand_positions[1]["start"][0] + CARD_WIDTH
        right_hand_left_edge = self.hand_positions[3]["start"][0]

        top_hand_bottom_edge = self.hand_positions[2]["start"][1] + CARD_HEIGHT
        bottom_hand_top_edge = self.hand_positions[0]["start"][1]

        center_x = (left_hand_right_edge + right_hand_left_edge) // 2
        center_y = (top_hand_bottom_edge + bottom_hand_top_edge) // 2
        self.trick_center = (center_x, center_y)

    def get_trick_position(self, player_idx: int) -> Tuple[int, int]:
        center_x, center_y = self.trick_center
        y_offset = CARD_HEIGHT // 2
        x_offset = CARD_WIDTH // 2

        if player_idx == 0:  # Bottom
            return (center_x - x_offset, center_y + y_offset)
        elif player_idx == 1:  # Left
            return (center_x - x_offset - CARD_WIDTH, center_y - y_offset)
        elif player_idx == 2:  # Top
            return (center_x - x_offset, center_y - y_offset - CARD_HEIGHT)
        else:  # Right
            return (center_x + x_offset, center_y - y_offset)

    def get_hand_position(self, player_idx: int, card_idx: int) -> Tuple[int, int]:
        pos = self.hand_positions[player_idx]
        start_x, start_y = pos["start"]
        offset_x, offset_y = pos["offset"]
        return (start_x + (card_idx * offset_x), start_y + (card_idx * offset_y))

    def get_player_info_position(self, player_idx: int) -> Tuple[int, int]:
        """Get position for player information display"""
        return self.player_positions[player_idx]
