# AI Chatbot

A full-stack AI chatbot: React + Vite frontend and Django REST backend with OpenAI.

## Structure

- **frontend/** — React (Vite), Tailwind CSS, chat UI
- **backend/** — Django REST API, OpenAI integration, SQLite for conversation history

## Quick start

1. **Backend** (from project root):

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set OPENAI_API_KEY and ALLOWED_ORIGINS
python manage.py migrate
python manage.py runserver
```

2. **Frontend** (in another terminal):

```bash
cd frontend
npm install
npm run dev
```

3. Open the frontend URL (e.g. http://localhost:5173) and chat. The frontend uses `http://localhost:8000` by default for the API.

## Docs

- [Frontend README](frontend/README.md) — setup, scripts, env
- [Backend README](backend/README.md) — API, env vars, migrations

## License

MIT
