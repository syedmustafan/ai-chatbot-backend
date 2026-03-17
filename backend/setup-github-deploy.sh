#!/usr/bin/env bash
# One-time setup: create GCP service account for GitHub Actions and set GitHub secrets.
# Run from repo root or backend/. Requires: gcloud (logged in), gh (logged in).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
KEY_FILE="$BACKEND_DIR/github-deploy-key.json"
REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

# Ensure we have gcloud and gh
if ! command -v gcloud &>/dev/null; then
  echo "Error: gcloud CLI not found. Install it: https://cloud.google.com/sdk/docs/install"
  exit 1
fi
if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI not found. Install it: brew install gh"
  exit 1
fi

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: Set GCP_PROJECT_ID or run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

SA_NAME="github-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Using GCP project: $PROJECT_ID"
echo "Creating service account: $SA_EMAIL"

# Create service account (ignore error if already exists)
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="GitHub Actions Deploy" \
  --project="$PROJECT_ID" 2>/dev/null || true

# Grant roles (project-level)
for ROLE in roles/run.admin roles/iam.serviceAccountUser roles/storage.admin; do
  echo "Granting $ROLE ..."
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --quiet
done

# Create JSON key (overwrites if exists)
echo "Creating JSON key at $KEY_FILE ..."
gcloud iam service-accounts keys create "$KEY_FILE" \
  --iam-account="$SA_EMAIL" \
  --project="$PROJECT_ID"

# Set GitHub secrets (run from repo root so gh uses this repo)
cd "$REPO_ROOT"
echo "Setting GitHub secret GCP_PROJECT_ID ..."
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID"
echo "Setting GitHub secret GCP_SA_KEY from key file ..."
gh secret set GCP_SA_KEY < "$KEY_FILE"
rm -f "$KEY_FILE"
echo "Removed $KEY_FILE (key is now in GitHub secrets only)."

echo ""
echo "Done. Optional: set in GitHub (Settings → Secrets → Actions):"
echo "  GCP_REGION          (default: us-central1)"
echo "  GCP_SERVICE_NAME    (default: ai-chatbot-backend)"
echo "  ALLOWED_ORIGINS     (comma-separated CORS origins)"
echo ""
echo "Push to prod or main to trigger deploy."
