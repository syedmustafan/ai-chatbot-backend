# AI Chatbot — Frontend

React + Vite frontend for the AI Chatbot. Uses Tailwind CSS and talks to the Django backend chat API.

## Prerequisites

- Node.js 18+
- Backend running at `http://localhost:8000` (or set `VITE_API_URL`)

## Setup

```bash
npm install
```

## Environment

Optional: create a `.env` in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

If unset, the app uses `http://localhost:8000` as the API base URL.

## Scripts

| Command    | Description                |
| ---------- | -------------------------- |
| `npm run dev`     | Start Vite dev server (default port 5173) |
| `npm run build`   | Production build to `dist/` |
| `npm run preview` | Preview production build    |

## Project structure

- `src/App.jsx` — Root app and layout
- `src/components/` — Chat UI (ChatBot, ChatWindow, ChatMessage, ChatInput, ChatHeader)
- `src/services/api.js` — `sendMessage()` calling `/api/chat/`
