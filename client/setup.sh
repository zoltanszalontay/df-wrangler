#!/bin/bash
echo "Creating virtual environment in venv/..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Setup complete. To activate the environment, run: source venv/bin/activate"
