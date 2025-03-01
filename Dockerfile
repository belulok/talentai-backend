# Base Python image
FROM python:3.11.6-slim

# Working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt /app
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the backend application code
COPY . /app

# Expose port for FastAPI
EXPOSE 8000

# Command to start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
