# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY app/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY app/ .

# Environment variable for the port
ENV PORT 5000

# Expose the port
EXPOSE $PORT

# Define environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the Flask application using gunicorn
# The port is now controlled by the PORT environment variable
CMD gunicorn --bind 0.0.0.0:$PORT app:app
