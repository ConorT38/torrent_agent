#!/bin/bash

# Check if the virtual environment exists
if [ ! -d "./venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
source ./venv/bin/activate

# Use the virtual environment's Python for all operations
venv_python="./venv/bin/python"

# Install dependencies
$venv_python -m pip install -r requirements.txt
$venv_python -m pip install wheel setuptools python-dotenv

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Build the wheel package
$venv_python setup.py bdist_wheel

# Simulate deployment by installing the wheel locally
$venv_python -m pip install ./dist/torrent_agent-0.1.0-py3-none-any.whl --force-reinstall

# Simulate service restart (replace with actual commands if needed)
echo "Simulating service restart..."
echo "Service restarted successfully."

# Run the module
$venv_python -m torrent_agent.torrent_agent