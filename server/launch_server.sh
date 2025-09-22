#!/bin/bash
cd "$(dirname "$0")"

echo "Activating virtual environment..."
source .venv/bin/activate

export TOKENIZERS_PARALLELISM=false

echo "Launching server..."
uvicorn app.main:app --reload
