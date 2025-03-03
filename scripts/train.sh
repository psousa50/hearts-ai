#!/bin/bash

TRAIN_FILE=$1

TRAIN_FILE=$(realpath $TRAIN_FILE)

cd ai-train
conda run -n tf-env python -u train.py $TRAIN_FILE