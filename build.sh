#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies using pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Optionally create a superuser if the flag is enabled (idempotent)
if [ "${CREATE_ADMIN_ON_DEPLOY}" = "true" ]; then
python manage.py create_admin || true
fi


