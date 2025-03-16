#!/bin/bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../transformer

source .venv/bin/activate
conda run -n tf-env 
PYTHONPATH=src uvicorn src.ai_service:app --reload 
