#!/bin/sh
# scripts/entrypoint.sh
#
# Runs inside the container on every startup.
# Waits for the DB to be ready, applies migrations, then starts Django.

set -e

echo "==> Waiting for database..."
until pg_isready -h "${DATABASE_HOST}" -p "${DATABASE_PORT}" -U "${DATABASE_USER}"; do
  sleep 1
done

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000