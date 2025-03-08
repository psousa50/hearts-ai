#!/bin/bash

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "state": {
      "previous_tricks": [
      {
        "cards": [
          { "suit": "H", "rank": 6 },
          { "suit": "H", "rank": 7 }
        ],
        "first_player_index": 3,
        "winner": 3,
        "score": 5
      }
      ],
      "current_trick": {
        "cards": [
          {"suit": "H", "rank": 3}
        ],
        "first_player_index": 3
      },
      "current_player_index": 3,
      "player_hand": [
        {"suit": "H", "rank": 2},
        {"suit": "H", "rank": 3},
        {"suit": "S", "rank": 4}
      ],
      "played_card": null
    },
    "valid_moves": [
      {"suit": "S", "rank": 4},
      {"suit": "H", "rank": 2}
    ]
  }'
