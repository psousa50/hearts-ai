#!/bin/bash

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "state": {
      "game_id": 1,
      "trick_number": 0,
      "previous_tricks": [],
      "current_trick_cards": [],
      "current_player_index": 3,
      "player_hand": [
        {"suit": "H", "rank": 2},
        {"suit": "H", "rank": 3},
        {"suit": "S", "rank": 4}
      ],
      "played_card": null
    },
    "valid_moves": [
      {"suit": "H", "rank": 2},
      {"suit": "H", "rank": 3}
    ]
  }'
