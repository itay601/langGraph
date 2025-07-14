# Use an official Python runtime as a parent image
FROM python:3.12.3-slim

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
# Copy the requirements file and install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Command to run the script
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]