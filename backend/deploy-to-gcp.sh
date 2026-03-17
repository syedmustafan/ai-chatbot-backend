#!/usr/bin/env bash
# Deploy AI Chatbot Backend to Google Cloud Run.
# Prerequisites: gcloud CLI, project set, secrets created (see DEPLOY_GCP.md).

set -e

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${GCP_SERVICE_NAME:-ai-chatbot-backend}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GCP_PROJECT_ID or run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

# Frontend URL for CORS (set before deploy or pass ALLOWED_ORIGINS)
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://ai-chatbot-frontend.vercel.app}"

echo "Deploying to project=$PROJECT_ID region=$REGION service=$SERVICE_NAME"
echo "CORS allowed_origins=$ALLOWED_ORIGINS"

# Use YAML env file so ALLOWED_ORIGINS can contain commas
ENV_FILE=$(mktemp)
trap "rm -f $ENV_FILE" EXIT
cat > "$ENV_FILE" << EOF
DEBUG: "False"
ALLOWED_HOSTS: "*"
ALLOWED_ORIGINS: "$ALLOWED_ORIGINS"
EOF

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest" \
  --env-vars-file="$ENV_FILE"

echo "Deploy complete. Service URL:"
gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)'
