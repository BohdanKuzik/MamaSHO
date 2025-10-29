#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies using pipenv (without dev for production)
pipenv install --ignore-pipfile

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

