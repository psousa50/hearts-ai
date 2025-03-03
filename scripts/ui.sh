#!/bin/bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../ui

sactivate
python game_visualizer.py --realtime  