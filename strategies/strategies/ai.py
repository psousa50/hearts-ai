import requests
from hearts_game_core.game_models import Card
from hearts_game_core.strategies import Strategy, StrategyGameState
from request_models.models import GameState, PredictRequest



class AIStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.endpoint = "http://localhost:8000/predict"

    def choose_card(self, strategy_game_state: StrategyGameState) -> Card:
        try:
            game_state = strategy_game_state.game_state
            state = GameState(
                previous_tricks=game_state.previous_tricks,
                current_trick=game_state.current_trick,
                current_player_index=game_state.current_player_index,
                player_hand=game_state.player_hand,
            )

            # Create prediction request
            predict_request = PredictRequest(
                state=state, valid_moves=game_state.valid_moves
            )
            json_data = predict_request.json()
            debug_print("Sending prediction request:", json.dumps(json_data, indent=2))

            # Send request to AI service
            response = requests.post(self.endpoint, json=json_data, timeout=5)
            response.raise_for_status()
            result = response.json()

            # debug_print("Received response from AI service:", json.dumps(result, indent=2))

            # Convert predicted move to Card
            if isinstance(result, dict) and "suit" in result and "rank" in result:
                predicted_card = Card(suit=result["suit"], rank=result["rank"])
                # Verify the predicted card is in valid_moves
                if predicted_card in game_state.valid_moves:
                    return predicted_card
                debug_print(f"AI predicted invalid move: {predicted_card}")
                raise ValueError("AI predicted invalid move")

            debug_print(f"Invalid prediction format: {result}")
            raise ValueError("Invalid prediction format")

        except Exception as e:
            raise ValueError(f"AI service error: {str(e)}")
