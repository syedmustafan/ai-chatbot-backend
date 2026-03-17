# Deploy AI Chatbot Backend to Google Cloud (Cloud Run + optional Cloud SQL)

This repo is the **backend only** (clone: [syedmustafan/ai-chatbot-backend](https://github.com/syedmustafan/ai-chatbot-backend)). All paths below are from the **repo root** (where `manage.py` and `Dockerfile` live).

Use the **gcloud** CLI. Replace `YOUR_GCP_PROJECT_ID` and region/values as needed.

## 1. Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and `gcloud` in PATH
- Logged in: `gcloud auth login`
- Project set: `gcloud config set project YOUR_GCP_PROJECT_ID`

## 2. Enable APIs

```bash
export PROJECT_ID=YOUR_GCP_PROJECT_ID
export REGION=us-central1

gcloud services enable run.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

**CI/CD (GitHub Actions):** For `gcloud run deploy --source`, `github-deploy@PROJECT_ID.iam.gserviceaccount.com` needs **Service Usage Consumer** (so APIs can be used), plus **Cloud Build**, **Run**, **Artifact Registry**, **Storage**, and **Service Account User**. From the repo root run `./setup-github-deploy.sh` for the full set, or grant missing roles:

```bash
SA="serviceAccount:github-deploy@${PROJECT_ID}.iam.gserviceaccount.com"
for ROLE in roles/serviceusage.serviceUsageConsumer roles/run.admin roles/iam.serviceAccountUser \
  roles/storage.admin roles/artifactregistry.writer roles/cloudbuild.builds.editor; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="$SA" --role="$ROLE" --quiet
done
```

If the workflow error mentions **`serviceusage.services.use`** or **Service Usage Consumer**, run (replace `YOUR_GCP_PROJECT_ID`):

```bash
gcloud projects add-iam-policy-binding YOUR_GCP_PROJECT_ID \
  --member="serviceAccount:github-deploy@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageConsumer" --quiet
```

Wait 2–5 minutes for IAM to propagate, then re-run the failed GitHub Action.

If deploy still fails with `PERMISSION_DENIED` (Cloud Build / default service account), the **Cloud Build** service account must push images and update Cloud Run:

```bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CB_SA}" --role="roles/artifactregistry.writer" --quiet
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CB_SA}" --role="roles/run.admin" --quiet
```

Optional (only if using Cloud SQL):

```bash
gcloud services enable sqladmin.googleapis.com
```

## 3. Create secrets in Secret Manager

Create secrets and grant Cloud Run access. Use strong values for production.

```bash
# OpenAI API key (required)
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=- --project="$PROJECT_ID"

# Django secret key (required; use a long random string)
echo -n "your-50-char-django-secret-key-here" | gcloud secrets create DJANGO_SECRET_KEY --data-file=- --project="$PROJECT_ID"
```

If you use **Cloud SQL**, create the DB password secret:

```bash
echo -n "your-db-password" | gcloud secrets create DB_PASSWORD --data-file=- --project="$PROJECT_ID"
```

Grant the default Cloud Run service account access to these secrets:

```bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in OPENAI_API_KEY DJANGO_SECRET_KEY; do
  gcloud secrets add-iam-policy-binding "$SECRET" \
    --member="serviceAccount:${SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT_ID"
done
# If using Cloud SQL:
# gcloud secrets add-iam-policy-binding DB_PASSWORD --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor" --project="$PROJECT_ID"
```

## 4. (Optional) Create Cloud SQL PostgreSQL instance

Only if you want a managed database instead of SQLite (recommended for production).

```bash
export INSTANCE_NAME=ai-chatbot-backend-db
export DB_NAME=chatbot
export DB_USER=chatbot_user

gcloud sql instances create "$INSTANCE_NAME" \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region="$REGION" \
  --project="$PROJECT_ID"

# Create database and user (password from Secret Manager or set here for create)
gcloud sql databases create "$DB_NAME" --instance="$INSTANCE_NAME" --project="$PROJECT_ID"
gcloud sql users create "$DB_USER" --instance="$INSTANCE_NAME" --password="CHANGE_ME_STRONG_PASSWORD" --project="$PROJECT_ID"
```

Get the instance connection name:

```bash
gcloud sql instances describe "$INSTANCE_NAME" --format='value(connectionName)' --project="$PROJECT_ID"
# Use this as CLOUD_SQL_CONNECTION_NAME in the next step.
```

For Cloud Run + Cloud SQL, `DATABASE_URL` must use the Unix socket. Example (replace placeholders):

- Host: `/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME`
- `DATABASE_URL`: `postgres://USER:PASSWORD@/DB_NAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME`

Store the password in Secret Manager as above and reference it in Cloud Run (e.g. `DB_PASSWORD`), then build `DATABASE_URL` in the container from env (e.g. `CLOUD_SQL_CONNECTION_NAME`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) or pass a single `DATABASE_URL` secret.

## 5. Deploy to Cloud Run

From the **repo root** (where `Dockerfile` and `manage.py` are):

```bash
cd /path/to/ai-chatbot-backend

export PROJECT_ID=YOUR_GCP_PROJECT_ID
export REGION=us-central1
export SERVICE_NAME=ai-chatbot-backend

# Build and deploy (no Cloud SQL)
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest" \
  --set-env-vars="DEBUG=False,ALLOWED_HOSTS=*" \
  --set-env-vars="ALLOWED_ORIGINS=https://YOUR_VERCEL_APP.vercel.app,https://YOUR_CUSTOM_DOMAIN.com"
```

- Replace `YOUR_VERCEL_APP` / `YOUR_CUSTOM_DOMAIN` with your frontend URL(s) for CORS.
- To use **Cloud SQL**, add:
  - `--add-cloudsql-instances=PROJECT_ID:REGION:INSTANCE_NAME`
  - And set `DATABASE_URL` (or the pieces) via env or a secret. Example env (if you build URL in code from env):  
    `DB_USER=chatbot_user,DB_NAME=chatbot,CLOUD_SQL_CONNECTION_NAME=PROJECT_ID:REGION:INSTANCE_NAME`  
    and `DB_PASSWORD` from Secret Manager:  
    `--set-secrets="...,DB_PASSWORD=DB_PASSWORD:latest"`

After deploy, note the **Service URL** (e.g. `https://ai-chatbot-backend-xxxxx-uc.a.run.app`). Use it as the frontend `VITE_API_URL`.

## 6. Run migrations (if using Cloud SQL)

If you use Cloud SQL, run migrations once (e.g. from Cloud Build or a one-off Cloud Run job):

```bash
# One-off job or use Cloud Shell with Cloud SQL Proxy
gcloud run jobs create chatbot-migrate --image=YOUR_IMAGE_URL --region="$REGION" \
  --set-secrets="SECRET_KEY=DJANGO_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
  --command="python" --args="manage.py,migrate,--noinput"
# Then run the job:
# gcloud run jobs execute chatbot-migrate --region="$REGION"
```

Or run migrations locally with Cloud SQL Proxy and `DATABASE_URL` set to the proxy.

## 7. Summary of secret env vars in GCP

| Env / Secret   | Description                    | Where to set in GCP                    |
|----------------|--------------------------------|----------------------------------------|
| OPENAI_API_KEY | OpenAI API key                 | Secret Manager → `--set-secrets`        |
| SECRET_KEY     | Django SECRET_KEY              | Secret Manager as DJANGO_SECRET_KEY    |
| DEBUG          | Set to `False` in production   | `--set-env-vars`                       |
| ALLOWED_HOSTS  | e.g. `*` or your domain        | `--set-env-vars`                       |
| ALLOWED_ORIGINS| Frontend URLs for CORS         | `--set-env-vars`                       |
| DATABASE_URL   | PostgreSQL URL (if Cloud SQL)  | Secret or env (build from DB_* + socket) |

After deployment, set the frontend’s `VITE_API_URL` (e.g. in Vercel) to the Cloud Run service URL.
