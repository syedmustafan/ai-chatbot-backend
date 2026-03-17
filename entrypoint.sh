#!/bin/sh
# Cloud Run sends traffic to the container's external interface — must bind 0.0.0.0, not 127.0.0.1.
set -e
PORT="${PORT:-8080}"
export PORT
python manage.py migrate --noinput
exec gunicorn \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --threads 8 \
  --timeout 0 \
  --access-logfile - \
  --error-logfile - \
  chatbot_project.wsgi:application
