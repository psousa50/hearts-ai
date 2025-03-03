#!/bin/bash

cd ai-train
conda run -n tf-env uvicorn ai_service:app --reload 