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
