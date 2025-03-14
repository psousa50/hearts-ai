from cards_models import Card, CompletedTrick, GameState, Trick


def extract_game_states(raw_data) -> list[GameState]:
    # Convert each card from [suit, rank] format to Card object format
    def convert_card(card_data):
        if isinstance(card_data, list) and len(card_data) == 2:
            suit, rank = card_data
            return Card(suit=suit, rank=rank)
        return None

    # Convert each completed trick from the raw format to CompletedTrick object
    def convert_completed_trick(trick_data):
        if isinstance(trick_data, list) and len(trick_data) >= 2:
            cards_data = trick_data[0] if len(trick_data) > 0 else []
            winner = trick_data[1] if len(trick_data) > 1 else 0
            # For first_player, we'll use a default of 0 if not provided
            first_player = 0  # Default value
            cards = [convert_card(card) for card in cards_data if card is not None]

            return CompletedTrick(
                cards=cards,
                winner=winner,
                score=0,  # Default value for score
                first_player_index=first_player,
            )
        return CompletedTrick(cards=[], winner=0, score=0, first_player_index=0)

    # Convert current trick from the raw format to Trick object
    def convert_current_trick(trick_data):
        if isinstance(trick_data, list) and len(trick_data) >= 2:
            cards_data = trick_data[0] if len(trick_data) > 0 else []
            first_player = trick_data[1] if len(trick_data) > 1 else 0

            cards = [convert_card(card) for card in cards_data if card is not None]

            return Trick(
                cards=cards,
                first_player_index=first_player,
            )
        return Trick(cards=[], first_player_index=0)

    # Convert each game state from raw format to GameState object
    def convert_game_state(game_state_data):
        # Based on the debug output, the game state has 5 elements:
        # [0]: Previous tricks (empty list in the example)
        # [1]: Current trick data [[cards], player_index]
        # [2]: Current player index
        # [3]: Player hand (list of cards)
        # [4]: Played card

        if not isinstance(game_state_data, list) or len(game_state_data) < 5:
            raise ValueError(f"Invalid game state format: {game_state_data}")

        # Extract data from the list format
        previous_tricks_data = game_state_data[0] if len(game_state_data) > 0 else []
        current_trick_data = game_state_data[1] if len(game_state_data) > 1 else [[], 0]
        current_player_index = game_state_data[2] if len(game_state_data) > 2 else 0
        player_hand_data = game_state_data[3] if len(game_state_data) > 3 else []
        played_card_data = game_state_data[4] if len(game_state_data) > 4 else None

        # Convert the data to the appropriate objects
        previous_tricks = [
            convert_completed_trick(trick) for trick in previous_tricks_data
        ]
        current_trick = convert_current_trick(current_trick_data)
        player_hand = [
            convert_card(card) for card in player_hand_data if card is not None
        ]
        played_card = convert_card(played_card_data) if played_card_data else None

        return GameState(
            previous_tricks=previous_tricks,
            current_trick=current_trick,
            current_player_index=current_player_index,
            player_hand=player_hand,
            played_card=played_card,
        )

    # Convert each game state from raw format to GameState object
    return [convert_game_state(game_state_data) for game_state_data in raw_data]
