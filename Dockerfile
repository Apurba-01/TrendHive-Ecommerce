# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application files
COPY . /app

# Set environment variables to avoid .pyc files and enable logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for PostgreSQL and other required packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose port 8000 for the application
EXPOSE 8000

# Use a non-root user for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Run Gunicorn to serve the Django app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "trendhive.wsgi:application"]

