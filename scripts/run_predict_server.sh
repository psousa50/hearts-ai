#!/bin/bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../ai-train

sactivate
conda run -n tf-env 
uvicorn ai_service:app --reload 
