#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt
python3 -m pip install wheel

# Build the wheel package
python3 setup.py bdist_wheel

# Simulate deployment by installing the wheel locally
pip install ./dist/torrent_agent-0.1.0-py3-none-any.whl --force-reinstall

# Simulate service restart (replace with actual commands if needed)
echo "Simulating service restart..."
echo "Service restarted successfully."

# Run the module
python3 -m torrent_agent.torrent_agent