#!/bin/sh
# Cloud Run: bind 0.0.0.0:$PORT. Migrations must succeed before serving traffic.
set -eu
PORT="${PORT:-8080}"
export PORT

echo "entrypoint: PORT=$PORT DATABASE_URL=${DATABASE_URL:+set}${DATABASE_URL:-unset}"

run_migrate_once() {
  if command -v timeout >/dev/null 2>&1; then
    timeout 120 python manage.py migrate --noinput
  else
    python manage.py migrate --noinput
  fi
}

# Cloud SQL socket can be slow on cold start; retry before failing the revision.
max_attempts=5
attempt=1
while [ "$attempt" -le "$max_attempts" ]; do
  echo "entrypoint: migrate attempt $attempt/$max_attempts"
  set +e
  run_migrate_once
  migrate_status=$?
  set -e
  if [ "$migrate_status" -eq 0 ]; then
    echo "entrypoint: migrate OK"
    break
  fi
  echo "entrypoint: migrate exited $migrate_status"
  if [ "$attempt" -eq "$max_attempts" ]; then
    echo "entrypoint: FATAL — migrations failed after $max_attempts attempts."
    echo "entrypoint: If using Cloud SQL: set DATABASE_URL secret, attach instance (--add-cloudsql-instances), grant Cloud Run SA roles/cloudsql.client"
    exit 1
  fi
  sleep $((attempt * 4))
  attempt=$((attempt + 1))
done

# SQLite allows only one writer; multiple Gunicorn workers cause random 500s
# ("database is locked") on /api/chat/ and /api/leads/ under concurrent traffic.
_db_url="${DATABASE_URL:-}"
case "$_db_url" in
  ''|*sqlite*) WORKERS=1 ;;
  *) WORKERS=2 ;;
esac
echo "entrypoint: gunicorn workers=$WORKERS (SQLite needs 1; Postgres can use 2+)"

exec python -m gunicorn \
  --bind "0.0.0.0:${PORT}" \
  --workers "$WORKERS" \
  --threads 8 \
  --timeout 0 \
  --access-logfile - \
  --error-logfile - \
  chatbot_project.wsgi:application
