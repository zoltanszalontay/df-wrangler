#!/bin/bash
echo "Creating virtual environment in .venv/..."
uv venv .venv

echo "Installing dependencies with uv..."
uv sync

echo "Setup complete. To activate the environment, run: source .venv/bin/activate"
