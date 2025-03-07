#!/bin/bash

NUM_GAMES=$1
SAVE_GAMES=$2
SAVE_AS_JSON=$3

if [ "$SAVE_GAMES" = "s" ]; then
    SAVE_GAMES_OPTION="--save-games"
else
    SAVE_GAMES_OPTION=""
fi

if [ "$SAVE_AS_JSON" = "j" ]; then
    SAVE_AS_JSON_OPTION="--save-as-json"
else
    SAVE_AS_JSON_OPTION=""
fi

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../cli

cargo run --bin hearts-cli -- generate-ai-training-data -n $NUM_GAMES $SAVE_GAMES_OPTION $SAVE_AS_JSON_OPTION