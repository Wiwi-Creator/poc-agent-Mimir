# Cloud Run Deployment

This guide deploys the local Mimir FastAPI prototype to Google Cloud Run.

## Assumptions

- Google Cloud project is already created.
- `gcloud` is installed and authenticated.
- Secret Manager is enabled.
- Your Groq API key is stored in Secret Manager.

Example secret name used below:

```text
GROQ_API_KEY
```

For LINE integration, this guide also assumes:

```text
LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET
```

Service name used below:

```text
mimir-api
```

Region used below:

```text
asia-east1
```

Change these values if your setup uses different names.

## Enable Required APIs

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

## Build And Deploy From Source

From the repo root:

```bash
gcloud run deploy mimir-api \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_MODEL=llama-3.1-8b-instant,APP_ENV=production,LOG_LEVEL=info \
  --set-secrets GROQ_API_KEY=GROQ_API_KEY:latest,LINE_CHANNEL_ACCESS_TOKEN=LINE_CHANNEL_ACCESS_TOKEN:latest,LINE_CHANNEL_SECRET=LINE_CHANNEL_SECRET:latest
```

Cloud Run will build the Dockerfile and deploy the service.

## Verify

After deployment, `gcloud` prints the service URL.

```bash
curl https://YOUR-CLOUD-RUN-URL/health
```

Expected response:

```json
{
  "status": "ok",
  "app_env": "production",
  "groq_model": "llama-3.1-8b-instant",
  "groq_configured": true
}
```

Test Hulk:

```bash
curl -X POST https://YOUR-CLOUD-RUN-URL/debug/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I benched 80kg for 5, 5, 4. What should I do next?"}'
```

## LINE Webhook

Set this URL in the LINE Developers Console:

```text
https://YOUR-CLOUD-RUN-URL/line/webhook
```

The webhook requires:

- `LINE_CHANNEL_ACCESS_TOKEN` for replying to LINE.
- `LINE_CHANNEL_SECRET` for verifying the `X-Line-Signature` header.

Use Secret Manager for both values.

## If Your Secret Has A Different Name

If the Secret Manager secret is named `groq-api-key`, deploy with:

```bash
--set-secrets GROQ_API_KEY=groq-api-key:latest
```

The left side is the environment variable name used by the app. The right side is the GCP Secret Manager secret name and version.

## Useful Commands

View service:

```bash
gcloud run services describe mimir-api --region asia-east1
```

View logs:

```bash
gcloud run services logs read mimir-api --region asia-east1
```

Update only environment variables:

```bash
gcloud run services update mimir-api \
  --region asia-east1 \
  --set-env-vars GROQ_MODEL=llama-3.1-8b-instant,APP_ENV=production,LOG_LEVEL=info
```
