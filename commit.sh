#!/bin/bash

NSG=$1

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
echo $SCRIPT_DIR
cd $SCRIPT_DIR

git add .
git commit -m "$NSG"
