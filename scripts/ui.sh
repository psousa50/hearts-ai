#!/bin/bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../ui

source .venv/bin/activate
python game_visualizer.py --realtime  