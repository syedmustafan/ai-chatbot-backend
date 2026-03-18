#!/usr/bin/env bash
# One-off: run Django migrations using the same image as your Cloud Run service.
# Use when you prefer a job over migrate-on-start, or to fix a DB without redeploying.
#
# Prerequisites:
#   gcloud auth, project set, Secret DATABASE_URL (+ DJANGO_SECRET_KEY as SECRET_KEY),
#   Cloud Run default SA has secretAccessor + cloudsql.client
#
# Usage:
#   export GCP_PROJECT_ID=...
#   export GCP_REGION=us-central1
#   export GCP_SERVICE_NAME=ai-chatbot-backend
#   export CLOUD_SQL_INSTANCE=PROJECT:REGION:INSTANCE   # optional but required for socket URL
#   ./scripts/run-migrations-cloud-run-job.sh

set -euo pipefail
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
SERVICE="${GCP_SERVICE_NAME:-ai-chatbot-backend}"
JOB_NAME="${GCP_SERVICE_NAME:-ai-chatbot-backend}-migrate"
INSTANCE="${CLOUD_SQL_INSTANCE:-}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GCP_PROJECT_ID or gcloud config set project"
  exit 1
fi

IMAGE=$(gcloud run services describe "$SERVICE" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format='value(spec.template.spec.containers[0].image)')

echo "Image: $IMAGE"

SECRETS="OPENAI_API_KEY=OPENAI_API_KEY:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest"
CMD=(gcloud run jobs deploy "$JOB_NAME" \
  --image="$IMAGE" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --set-secrets="$SECRETS" \
  --set-env-vars="DEBUG=False,ALLOWED_HOSTS=*" \
  --command=python \
  --args=manage.py,migrate,--noinput \
  --max-retries=2 \
  --task-timeout=15m \
  --quiet)

if [[ -n "$INSTANCE" ]]; then
  CMD+=(--set-cloudsql-instances="$INSTANCE")
fi

"${CMD[@]}"

echo "Executing job..."
gcloud run jobs execute "$JOB_NAME" --region="$REGION" --project="$PROJECT_ID" --wait

echo "Migrations job finished."
