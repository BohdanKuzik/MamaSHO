#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies using pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Make and run migrations
python manage.py makemigrations --no-input || true
python manage.py migrate

# Optionally create a superuser if the flag is enabled (idempotent)
case "${CREATE_ADMIN_ON_DEPLOY,,}" in
  true|1|yes)
    python manage.py create_admin || true
    ;;
esac


