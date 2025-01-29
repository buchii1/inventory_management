# Use the official Python 3.10-slim image as the base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app

# Make migrations and migrate the database
RUN python manage.py makemigrations inventory
RUN python manage.py migrate

# Collect static files (for production, if needed)
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Create a script to run both Gunicorn and Celery
RUN echo '#!/bin/bash\n\
gunicorn inventory_api.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 &\n\
celery -A inventory_api worker --loglevel=info' > /start.sh

# Make the script executable
RUN chmod +x /start.sh

# Default CMD for the Django application
CMD ["/start.sh"]
