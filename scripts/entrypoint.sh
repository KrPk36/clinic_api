#!/bin/sh
# scripts/entrypoint.sh
#
# Runs inside the container on every startup.
# Waits for the DB to be ready, applies migrations, then starts Django.

set -e

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> Starting Django development server with hot-reload..."
exec python manage.py runserver 0.0.0.0:8000