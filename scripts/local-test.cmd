:: Create a virtual environment
python -m venv venv

:: Activate the virtual environment
call venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt
python -m pip install wheel

:: Build the wheel package
python setup.py bdist_wheel

:: Simulate deployment by installing the wheel locally
pip install .\dist\torrent_agent-0.1.0-py3-none-any.whl --force-reinstall

:: Simulate service restart (replace with actual commands if needed)
echo Simulating service restart...
echo Service restarted successfully.

:: Run the module
python -m torrent_agent.torrent_agent
