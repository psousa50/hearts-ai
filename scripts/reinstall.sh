#!/bin/bash

rm -rf .venv
find . -name "pyproject.toml" -execdir pip install -e . \;  
