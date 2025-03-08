#!/bin/bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../cli

cargo run --bin hearts-cli -- generate-games --num-games "$@"