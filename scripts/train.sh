#!/bin/bash

TRAIN_FILE=$1

TRAIN_FILE=$(realpath $TRAIN_FILE)

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd $SCRIPT_DIR/../ai-train

conda run -n tf-env
 
python -u src/train.py $TRAIN_FILE