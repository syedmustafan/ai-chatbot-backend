# AI Chatbot — Backend

[![Deploy Backend to GCP](https://github.com/syedmustafan/ai-chatbot-backend/actions/workflows/deploy-backend.yml/badge.svg)](https://github.com/syedmustafan/ai-chatbot-backend/actions/workflows/deploy-backend.yml)

Django REST API for the AI Chatbot. Handles chat messages, conversation history, and OpenAI integration.

**Repo:** [github.com/syedmustafan/ai-chatbot-backend](https://github.com/syedmustafan/ai-chatbot-backend) (backend-only; use from repo root).

## Deploy to Google Cloud (CI/CD)

1. Enable APIs and create Secret Manager secrets — see **[DEPLOY_GCP.md](./DEPLOY_GCP.md)**.
2. From **this repo root** (same folder as `manage.py`):

   ```bash
   ./setup-github-deploy.sh
   ```

   Requires [gcloud](https://cloud.google.com/sdk) and [GitHub CLI](https://cli.github.com/) (`gh auth login` in this repo).

3. Push to **`main`** or **`prod`** — GitHub Actions deploys to Cloud Run (workflow: `.github/workflows/deploy-backend.yml`).

Manual one-off deploy: `./deploy-to-gcp.sh` (from repo root, after `gcloud auth` and secrets exist).

## Prerequisites

- Python 3.10+
- OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys)

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment template and configure:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

- `OPENAI_API_KEY` — Your OpenAI API key (required)
- `ALLOWED_ORIGINS` — Comma-separated frontend URLs (e.g. `http://localhost:5173`)
- `SECRET_KEY` — Django secret (use a random string in production)

4. Run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

API will be at `http://localhost:8000`. Chat endpoint: `POST /api/chat/`.

## Environment variables

| Variable           | Required | Description                                      |
| ------------------ | -------- | ------------------------------------------------ |
| `OPENAI_API_KEY`   | Yes      | OpenAI API key                                   |
| `ALLOWED_ORIGINS`  | No       | CORS origins (default includes localhost:5174, 3000) |
| `SECRET_KEY`       | No       | Django secret (default: insecure dev value)      |
| `DEBUG`            | No       | Debug mode (default: True)                       |
| `OPENAI_MODEL`     | No       | Model name (default: gpt-3.5-turbo)              |
| `OPENAI_SYSTEM_PROMPT` | No  | Custom system prompt for the assistant           |

## API

- **POST /api/chat/**  
  Body: `{ "message": "user text", "conversation_id": "uuid" }`  
  Returns: `{ "success", "response", "conversation_id", "timestamp" }`

Conversation history is stored in SQLite; pass `conversation_id` to continue a thread.
