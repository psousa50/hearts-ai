#!/bin/bash

NUM_GAMES=$1

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../cli

cargo run --bin hearts-cli -- generate-ai-training-data -n $NUM_GAMES