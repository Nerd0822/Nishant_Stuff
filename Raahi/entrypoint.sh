#!/bin/sh
# Raahi container entrypoint. Keeps docker-compose.yml readable: each
# service just passes a short role instead of a long shell one-liner.
#
# Usage:
#   entrypoint.sh web [--migrate]   # gunicorn (+ migrate + collectstatic)
#   entrypoint.sh celery            # celery worker
#   entrypoint.sh <anything else>   # exec'd directly (e.g. shell passthrough)
#
# Only raahi1 gets --migrate, so migrations/collectstatic never race
# on the shared volumes.
set -e

ROLE="${1:-web}"

if [ "$ROLE" = "web" ] && [ "${2:-}" = "--migrate" ]; then
    python manage.py migrate
    python manage.py collectstatic --noinput
fi

case "$ROLE" in
    web)
        exec gunicorn CORE.asgi:application \
            --bind 0.0.0.0:8000 \
            --workers 2 \
            -k uvicorn.workers.UvicornWorker \
            --access-logfile - \
            --error-logfile -
        ;;
    celery)
        exec celery -A CORE worker -l info
        ;;
    *)
        exec "$@"
        ;;
esac
