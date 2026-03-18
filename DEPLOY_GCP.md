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

## 6. Migrations

**On every container start**, `entrypoint.sh` runs `python manage.py migrate`. If migrations fail (wrong `DATABASE_URL`, Cloud SQL not attached, IAM), the **revision fails to start** so you fix config instead of serving a broken API.

### Fix: `no such table: chatbot_conversation`

That message is from **SQLite**: Cloud Run had **no `DATABASE_URL`**, so Django used ephemeral `/tmp/db.sqlite3`. If migrate ever failed, the old entrypoint still started the web server → empty DB → missing tables.

**Do this for production:**

1. **Create Cloud SQL Postgres** (§4) and note `CONNECTION_NAME` (`project:region:instance`).

2. **Store `DATABASE_URL` in Secret Manager** (password URL-encoded if it has special chars):

   ```bash
   # Example socket URL for Cloud SQL Auth:
   echo -n 'postgres://chatbot_user:YOUR_PASSWORD@/chatbot?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME' | \
     gcloud secrets create DATABASE_URL --data-file=- --project="$PROJECT_ID" 2>/dev/null || \
     echo -n 'postgres://...' | gcloud secrets versions add DATABASE_URL --data-file=-
   ```

3. **Grant the Cloud Run service account** access to the secret and Cloud SQL:

   ```bash
   PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
   RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
   gcloud secrets add-iam-policy-binding DATABASE_URL \
     --member="serviceAccount:${RUN_SA}" --role="roles/secretmanager.secretAccessor" --project="$PROJECT_ID"
   gcloud projects add-iam-policy-binding "$PROJECT_ID" \
     --member="serviceAccount:${RUN_SA}" --role="roles/cloudsql.client" --quiet
   ```

4. **Wire deploy (GitHub Actions):** add repository secret **`GCLOUD_SQL_INSTANCE`** = your `PROJECT:REGION:INSTANCE` (same as connection name). The workflow mounts `DATABASE_URL` and `--add-cloudsql-instances`. Push to `main`/`prod` to redeploy.

5. **Or patch Cloud Run once from CLI** (then add secrets to CI so the next deploy does not drop them):

   ```bash
   gcloud run services update ai-chatbot-backend --region="$REGION" --project="$PROJECT_ID" \
     --add-cloudsql-instances="PROJECT:REGION:INSTANCE" \
     --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
     --update-env-vars="DEBUG=False,ALLOWED_HOSTS=*,ALLOWED_ORIGINS=https://your-app.vercel.app"
   ```

   Redeploy or wait for a new revision; startup will run migrations on Postgres.

### One-off migrate job (optional)

From repo root, after the service image exists:

```bash
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export CLOUD_SQL_INSTANCE=PROJECT:REGION:INSTANCE
./scripts/run-migrations-cloud-run-job.sh
```

Or run migrations locally with [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy) and `DATABASE_URL` pointing at `127.0.0.1`.

## 7. Summary of secret env vars in GCP

| Env / Secret   | Description                    | Where to set in GCP                    |
|----------------|--------------------------------|----------------------------------------|
| OPENAI_API_KEY | OpenAI API key                 | Secret Manager → `--set-secrets`        |
| SECRET_KEY     | Django SECRET_KEY              | Secret Manager as DJANGO_SECRET_KEY    |
| DEBUG          | Set to `False` in production   | `--set-env-vars`                       |
| ALLOWED_HOSTS  | e.g. `*` or your domain        | `--set-env-vars`                       |
| ALLOWED_ORIGINS| Frontend URLs for CORS         | `--set-env-vars`                       |
| DATABASE_URL   | PostgreSQL URL (if Cloud SQL)  | Secret or env (build from DB_* + socket) |
| PUBLIC_BASE_URL| **HTTPS** origin of this API (no trailing slash), e.g. `https://your-service-xxxxx.run.app` | `--update-env-vars` — **required for Twilio webhooks** |
| TWILIO_AUTH_TOKEN | Twilio Auth Token (validates webhook signatures) | Secret Manager or env |
| LEADS_API_KEY | Protects `GET /api/leads/` (must match frontend `VITE_LEADS_API_KEY`) | GitHub secret → deploy env, or `--update-env-vars` |

After deployment, set the frontend’s `VITE_API_URL` (e.g. in Vercel) to the Cloud Run service URL.

### Leads API (`GET /api/leads/`)

In production the leads list requires a shared secret:

1. Choose a long random string (e.g. `openssl rand -hex 16`).
2. **GitHub** (backend repo): add repository secret **`LEADS_API_KEY`** with that value, then redeploy (`main` / `prod`). The workflow passes it to Cloud Run.
3. **Vercel** (frontend): set **`VITE_LEADS_API_KEY`** to the **same** value and redeploy the frontend so requests include `X-API-Key`.

Without `LEADS_API_KEY` on Cloud Run, the API returns *“Leads API requires LEADS_API_KEY in production”* even if the client sends a key.

**500 on `/api/leads/` with SQLite:** The default deploy without `DATABASE_URL` uses SQLite on `/tmp` with **one Gunicorn worker** (multi-worker + SQLite causes `database is locked`). For real traffic, use **PostgreSQL** (Cloud SQL + `DATABASE_URL`) so you can scale workers safely.

**Manual Cloud Run update** (if not using the new workflow yet):

```bash
gcloud run services update "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" \
  --update-env-vars="LEADS_API_KEY=YOUR_SAME_SECRET_AS_FRONTEND"
```

## 8. Twilio inbound voice (AI phone intake)

1. **Env on Cloud Run** (in addition to the table above):
   - `PUBLIC_BASE_URL` = your service URL, e.g. `https://ai-chatbot-backend-xxxxx-uc.a.run.app` (must match what Twilio calls — no path).
   - `TWILIO_AUTH_TOKEN` = from [Twilio Console](https://console.twilio.com/) (keep secret).

2. **Twilio Console**
   - Buy a voice-capable number (check [Twilio voice coverage](https://www.twilio.com/voice) for your country).
   - **Phone number → Voice configuration → A call comes in**: Webhook, **POST**, URL:
     - `https://YOUR_HOST/api/twilio/voice/incoming/`
   - Save.

3. **Flow**
   - Twilio hits `incoming/` → Django creates a **Lead** (`source=phone`) and returns TwiML: **Say** + **Gather** (speech).
   - Each utterance POSTs to `gather/` → same intake LLM as web → **Say** + **Gather** until all fields are filled, then **Say** + **Hangup**.
   - Leads appear in Django **admin** (`/admin/`).

4. **Local testing**
   - Use [ngrok](https://ngrok.com/) (or similar) HTTPS URL as `PUBLIC_BASE_URL` and set the Twilio webhook to your tunnel + `/api/twilio/voice/incoming/`.
   - If `TWILIO_AUTH_TOKEN` is unset and `DEBUG=True`, signature checks are skipped (dev only).

5. **Model**
   - Use a model that supports JSON mode (e.g. `gpt-4o-mini`) via `OPENAI_MODEL` for reliable field extraction.

## Troubleshooting: “failed to start and listen on PORT=8080”

1. **Bind address** — Gunicorn must listen on **`0.0.0.0`**, not only `127.0.0.1`. This repo’s `entrypoint.sh` uses `--bind "0.0.0.0:${PORT}"`.
2. **`migrate` failing** — If the container exits before Gunicorn starts, check revision logs: DB URL / network (e.g. Cloud SQL) can make `migrate` hang or fail.
3. **`ALLOWED_HOSTS: "*"`** — Django does not accept a literal `*` for all hosts. For Cloud Run, use `.run.app` (handled automatically when you set `ALLOWED_HOSTS` to `*` in the workflow) or list real hostnames.
