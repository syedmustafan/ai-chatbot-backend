#!/usr/bin/env bash
# One-time setup: GCP service account for GitHub Actions + GitHub secrets.
#
# Run from THIS REPO ROOT (where manage.py lives):
#   ./setup-github-deploy.sh
#
# Or from a monorepo subfolder backend/:
#   ./setup-github-deploy.sh
#
# Requires: gcloud (logged in), gh (logged in to the target GitHub repo).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
KEY_FILE="$BACKEND_DIR/github-deploy-key.json"

# Standalone repo (manage.py next to this script) vs monorepo (script in backend/)
if [[ -f "$SCRIPT_DIR/manage.py" ]]; then
  REPO_ROOT="$SCRIPT_DIR"
else
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

if ! command -v gcloud &>/dev/null; then
  echo "Error: gcloud CLI not found. https://cloud.google.com/sdk/docs/install"
  exit 1
fi
if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI not found. Install: brew install gh"
  exit 1
fi

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: Set GCP_PROJECT_ID or: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

SA_NAME="github-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Using GCP project: $PROJECT_ID"
echo "GitHub repo root for secrets: $REPO_ROOT"
echo "Creating service account: $SA_EMAIL"

gcloud iam service-accounts create "$SA_NAME" \
  --display-name="GitHub Actions Deploy" \
  --project="$PROJECT_ID" 2>/dev/null || true

for ROLE in roles/run.admin roles/iam.serviceAccountUser roles/storage.admin \
  roles/artifactregistry.writer roles/cloudbuild.builds.editor; do
  echo "Granting $ROLE ..."
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --quiet
done

echo "Creating JSON key at $KEY_FILE ..."
gcloud iam service-accounts keys create "$KEY_FILE" \
  --iam-account="$SA_EMAIL" \
  --project="$PROJECT_ID"

cd "$REPO_ROOT"
echo "Setting GitHub secret GCP_PROJECT_ID ..."
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID"
echo "Setting GitHub secret GCP_SA_KEY ..."
gh secret set GCP_SA_KEY < "$KEY_FILE"
rm -f "$KEY_FILE"

echo ""
echo "Done. Optional secrets (Settings → Secrets → Actions):"
echo "  GCP_REGION       (default: us-central1)"
echo "  GCP_SERVICE_NAME (default: ai-chatbot-backend)"
echo "  ALLOWED_ORIGINS  (comma-separated CORS origins)"
echo ""
echo "Push to main or prod to deploy."
