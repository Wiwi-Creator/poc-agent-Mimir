# Mimir Multi-Agent System

Mimir is a FastAPI supervisor that routes requests to a small team of
Groq-powered specialist agents:

- **Mimir:** orchestrator and conversation owner
- **Hulk:** workout and nutrition
- **Dragonite:** travel planning
- **Porygon:** personal finance
- **Sage:** career development
- **Mewtwo:** technology information
- **Rotom:** meeting support

## Run Locally

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/docs
```

The root page is a simple agent dashboard and chat console. It uses the same
`POST /debug/chat` flow as LINE, so dashboard and messaging behavior stay
aligned.

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

List enabled agents:

```bash
curl http://127.0.0.1:8000/api/agents
```

## Environment

Copy `.env.example` to `.env` and add your Groq API key.

```env
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
```

Do not commit `.env`.

## Deploy

Cloud Run deployment notes are in [docs/cloud-run-deployment.md](docs/cloud-run-deployment.md).

Quick deploy:

```bash
chmod +x scripts/deploy-cloud-run.sh
./scripts/deploy-cloud-run.sh
```

Override defaults:

```bash
PROJECT_ID=your-project REGION=asia-east1 SERVICE_NAME=mimir-api ./scripts/deploy-cloud-run.sh
```

## LINE

Set your LINE webhook URL to:

```text
https://YOUR-CLOUD-RUN-URL/line/webhook
```

The service needs both LINE values:

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`

Store them in Secret Manager for Cloud Run, and in local `.env` for local testing.
