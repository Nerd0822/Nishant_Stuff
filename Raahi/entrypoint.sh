#!/bin/bash
set -e

export PATH="/home/Raahi_dev/.local/bin:$PATH"

# Fail fast if required configuration is missing (prevents Django
# falling back to a local Unix socket with HOST=None).
: "${DB_NAME:?Missing DB_NAME}"
: "${DB_USER:?Missing DB_USER}"
: "${DB_PASSWORD:?Missing DB_PASSWORD}"
: "${DB_HOST:?Missing DB_HOST}"
: "${DB_PORT:?Missing DB_PORT}"
: "${SECRET_KEY:?Missing SECRET_KEY}"

export PGPASSWORD="${DB_PASSWORD}"

# Wait for Postgres even though compose uses service_healthy; this covers
# restarts and race conditions without failing migrate immediately.
echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
for i in $(seq 1 30); do
  if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; then
    echo "Postgres is ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Postgres did not become ready in time." >&2
    exit 1
  fi
  sleep 2
done

# Ensure staticfiles directory exists (safety net for volume mounts)
mkdir -p /Raahi/staticfiles

python3 Backend/manage.py makemigrations
python3 Backend/manage.py migrate
python3 Backend/manage.py collectstatic --noinput
cd Backend
exec gunicorn SERVER.wsgi:application --bind 0.0.0.0:8000 --workers 3
