#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies using pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist (only creates if not exists)
python manage.py create_admin || true

