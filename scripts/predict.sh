#!/bin/bash

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": 1,
    "trick_number": 0,
    "previous_tricks": [],
    "current_trick_cards": [],
    "current_player_index": 3,
    "hand": [["H", 2], ["H", 3], ["S", 4]],
    "valid_moves": [["H", 2], ["H", 3]]
  }'
