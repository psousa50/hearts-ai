from typing import Dict, Tuple

class LayoutManager:
    def __init__(self, window_width: int, window_height: int):
        self.window_width = window_width
        self.window_height = window_height
        self.trick_center = (window_width // 2, window_height // 2)
        
        # Player positions (center points for names and scores)
        self.player_positions = {
            0: (window_width // 2, window_height - 50),  # Bottom
            1: (200, window_height // 2),  # Left
            2: (window_width // 2, 30),  # Top
            3: (window_width - 200, window_height // 2),  # Right
        }

        # Hand display positions and offsets
        card_overlap = 30
        self.hand_positions = {
            0: {
                "start": (window_width // 4, window_height - 200),  # Bottom
                "offset": (card_overlap, 0),
            },
            1: {
                "start": (100, window_height // 4),  # Left
                "offset": (0, card_overlap),
            },
            2: {
                "start": (window_width // 4, 70),  # Top
                "offset": (card_overlap, 0),
            },
            3: {
                "start": (window_width - 120, window_height // 4),  # Right
                "offset": (0, card_overlap),
            },
        }

    def get_trick_position(self, player_idx: int) -> Tuple[int, int]:
        """Calculate position for a card in the trick based on player position"""
        center_x, center_y = self.trick_center
        offset = 80  # Distance from center

        if player_idx == 0:  # Bottom
            return (center_x, center_y + offset)
        elif player_idx == 1:  # Left
            return (center_x - offset, center_y)
        elif player_idx == 2:  # Top
            return (center_x, center_y - offset)
        else:  # Right
            return (center_x + offset, center_y)

    def get_hand_position(self, player_idx: int, card_idx: int) -> Tuple[int, int]:
        """Calculate position for a card in a player's hand"""
        pos = self.hand_positions[player_idx]
        start_x, start_y = pos["start"]
        offset_x, offset_y = pos["offset"]
        return (start_x + (card_idx * offset_x), start_y + (card_idx * offset_y))

    def get_player_info_position(self, player_idx: int) -> Tuple[int, int]:
        """Get position for player information display"""
        return self.player_positions[player_idx]
