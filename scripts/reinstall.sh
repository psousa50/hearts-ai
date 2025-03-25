#!/bin/bash

rm -rf .venv
python -m venv .venv
source .venv/bin/activate
find . -name "pyproject.toml" -execdir pip install -e . \;  
pip install --upgrade pip
