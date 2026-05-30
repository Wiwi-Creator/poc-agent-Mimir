# Mimir Local Prototype

Mimir is a local FastAPI supervisor agent. The first sub-agent is Hulk, a fitness coach and nutrition analyzer powered by Groq.

## Run Locally

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Chat with Mimir:

```bash
curl -X POST http://127.0.0.1:8000/debug/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I benched 80kg for 5, 5, 4. What should I do next?"}'
```

## Environment

Copy `.env.example` to `.env` and add your Groq API key.

```env
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
```

Do not commit `.env`.
