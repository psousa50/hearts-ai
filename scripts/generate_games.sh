#!/bin/bash

NUM_GAMES=$1

cd cli
cargo run --bin hearts-cli -- generate-games --num-games $NUM_GAMES