#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-ai-production-487311}"
REGION="${REGION:-asia-east1}"
SERVICE_NAME="${SERVICE_NAME:-mimir-api}"
GROQ_MODEL="${GROQ_MODEL:-llama-3.1-8b-instant}"
GROQ_SECRET_NAME="${GROQ_SECRET_NAME:-GROQ_API_KEY}"
LINE_CHANNEL_ACCESS_TOKEN_SECRET_NAME="${LINE_CHANNEL_ACCESS_TOKEN_SECRET_NAME:-LINE_CHANNEL_ACCESS_TOKEN}"
LINE_CHANNEL_SECRET_SECRET_NAME="${LINE_CHANNEL_SECRET_SECRET_NAME:-LINE_CHANNEL_SECRET}"
APP_ENV="${APP_ENV:-production}"
LOG_LEVEL="${LOG_LEVEL:-info}"
ALLOW_UNAUTHENTICATED="${ALLOW_UNAUTHENTICATED:-true}"
INCLUDE_LINE_SECRETS="${INCLUDE_LINE_SECRETS:-true}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is required but was not found in PATH." >&2
  exit 1
fi

PROJECT_NUMBER="$(
  gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)'
)"
RUNTIME_SERVICE_ACCOUNT="${RUNTIME_SERVICE_ACCOUNT:-${PROJECT_NUMBER}-compute@developer.gserviceaccount.com}"

require_secret() {
  local secret_name="$1"
  if ! gcloud secrets describe "${secret_name}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    echo "Missing Secret Manager secret: ${secret_name}" >&2
    echo "Create it before deploying, then rerun this script." >&2
    exit 1
  fi
}

grant_secret_access() {
  local secret_name="$1"
  gcloud secrets add-iam-policy-binding "${secret_name}" \
    --project "${PROJECT_ID}" \
    --member "serviceAccount:${RUNTIME_SERVICE_ACCOUNT}" \
    --role "roles/secretmanager.secretAccessor" \
    --quiet >/dev/null
}

echo "Deploying ${SERVICE_NAME} to Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Model: ${GROQ_MODEL}"
echo "Groq secret: ${GROQ_SECRET_NAME}"
echo "Runtime service account: ${RUNTIME_SERVICE_ACCOUNT}"
if [[ "${INCLUDE_LINE_SECRETS}" == "true" ]]; then
  echo "LINE access token secret: ${LINE_CHANNEL_ACCESS_TOKEN_SECRET_NAME}"
  echo "LINE channel secret secret: ${LINE_CHANNEL_SECRET_SECRET_NAME}"
fi

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  --project "${PROJECT_ID}"

AUTH_FLAG="--allow-unauthenticated"
if [[ "${ALLOW_UNAUTHENTICATED}" != "true" ]]; then
  AUTH_FLAG="--no-allow-unauthenticated"
fi

require_secret "${GROQ_SECRET_NAME}"
grant_secret_access "${GROQ_SECRET_NAME}"

SECRET_ARGS=("GROQ_API_KEY=${GROQ_SECRET_NAME}:latest")
if [[ "${INCLUDE_LINE_SECRETS}" == "true" ]]; then
  require_secret "${LINE_CHANNEL_ACCESS_TOKEN_SECRET_NAME}"
  require_secret "${LINE_CHANNEL_SECRET_SECRET_NAME}"
  grant_secret_access "${LINE_CHANNEL_ACCESS_TOKEN_SECRET_NAME}"
  grant_secret_access "${LINE_CHANNEL_SECRET_SECRET_NAME}"
  SECRET_ARGS+=(
    "LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN_SECRET_NAME}:latest"
    "LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET_SECRET_NAME}:latest"
  )
fi

SECRETS_CSV="$(IFS=,; echo "${SECRET_ARGS[*]}")"

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  "${AUTH_FLAG}" \
  --set-env-vars "GROQ_MODEL=${GROQ_MODEL},APP_ENV=${APP_ENV},LOG_LEVEL=${LOG_LEVEL}" \
  --set-secrets "${SECRETS_CSV}"

SERVICE_URL="$(
  gcloud run services describe "${SERVICE_NAME}" \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --format='value(status.url)'
)"

echo
echo "Deployed:"
echo "${SERVICE_URL}"
echo
echo "Health check:"
echo "curl ${SERVICE_URL}/health"
