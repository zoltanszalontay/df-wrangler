#!/bin/bash
cd "$(dirname "$0")"

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Launching server..."
uvicorn app.main:app --reload
