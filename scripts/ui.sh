#!/bin/bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../ui

source .venv/bin/activate
conda run -n tf-env python src/game_visualizer.py $0