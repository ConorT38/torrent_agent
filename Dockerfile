# Use the official Python 3.9 slim image as the base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Build the wheel for the project
RUN python setup.py bdist_wheel && pip install dist/*.whl

# Set the default command to invoke the module
CMD ["python", "-m", "torrent_agent.torrent_agent"]