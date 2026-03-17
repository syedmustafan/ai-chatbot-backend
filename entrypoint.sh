#!/bin/sh
# Cloud Run: bind 0.0.0.0:$PORT. Migrate must not hang forever (unreachable DB blocks the port).
set -eu
PORT="${PORT:-8080}"
export PORT

echo "entrypoint: PORT=$PORT"

set +e
if command -v timeout >/dev/null 2>&1; then
  timeout 180 python manage.py migrate --noinput
else
  python manage.py migrate --noinput
fi
migrate_status=$?
set -e

if [ "$migrate_status" -ne 0 ]; then
  echo "entrypoint: migrate exited $migrate_status (timed out, failed, or DB unreachable) — starting web server anyway"
fi

exec python -m gunicorn \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --threads 8 \
  --timeout 0 \
  --access-logfile - \
  --error-logfile - \
  chatbot_project.wsgi:application
