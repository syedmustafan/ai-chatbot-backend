# AI Chatbot — Backend

Django REST API for the AI Chatbot. Handles chat messages, conversation history, and OpenAI integration.

**Frontend repo:** [ai-chatbot-frontend](https://github.com/syedmustafan/ai-chatbot-frontend) — React UI that consumes this API.

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
