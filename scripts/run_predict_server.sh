#!/bin/bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../predict_server

source .venv/bin/activate
conda run -n tf-env 
PYTHONPATH=src uvicorn predict_server.main:app --reload 
