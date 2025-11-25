#!/bin/bash
# Startup script for Render deployment

set -e  # Exit on error

echo "Starting Django application..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Create cache table if it doesn't exist
echo "Creating cache table..."
python manage.py createcachetable || true

echo "Starting Gunicorn..."
# Start Gunicorn with the PORT environment variable from Render
exec gunicorn procure.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

