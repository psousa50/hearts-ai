#!/bin/bash

NUM_GAMES=$1

cd cli
cargo run --bin hearts-cli -- generate-ai-training-data -n $NUM_GAMES