#!/bin/bash
# deploy.sh — Automated deployment to Google Cloud Run
# Usage: ./deploy.sh

set -euo pipefail

# ============================================================
# Configuration
# ============================================================
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}"
REGION="us-central1"
SERVICE_NAME="live-ai-voice-translator"

echo "============================================"
echo "  Live AI Voice Translator — Cloud Deployment"
echo "============================================"
echo ""
echo "Project:  ${PROJECT_ID}"
echo "Region:   ${REGION}"
echo "Service:  ${SERVICE_NAME}"
echo ""

# ============================================================
# Step 1: Enable required Google Cloud APIs
# ============================================================
echo "[1/5] Enabling required Google Cloud APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    texttospeech.googleapis.com \
    translate.googleapis.com \
    artifactregistry.googleapis.com \
    --project="${PROJECT_ID}"
echo "  APIs enabled."

# ============================================================
# Step 2: Set project
# ============================================================
echo "[2/5] Setting active project..."
gcloud config set project "${PROJECT_ID}"

# ============================================================
# Step 3: Deploy to Cloud Run (source-based)
# ============================================================
echo "[3/5] Building and deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --source=. \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=5 \
    --set-env-vars="GOOGLE_API_KEY=${GOOGLE_API_KEY:-}" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --timeout=300

echo "  Deployed to Cloud Run."

# ============================================================
# Step 4: Get the service URL
# ============================================================
echo "[4/5] Retrieving service URL..."
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --format="value(status.url)")
echo ""
echo "============================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================"
echo ""
echo "  Service URL: ${SERVICE_URL}"
echo ""

# ============================================================
# Step 5: Verify deployment
# ============================================================
echo "[5/5] Verifying deployment..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/api/health" || echo "000")
if [ "${STATUS_CODE}" = "200" ]; then
    echo "  Health check PASSED (HTTP ${STATUS_CODE})"
else
    echo "  Health check returned HTTP ${STATUS_CODE} (may need a moment to start)"
fi

echo ""
echo "Done! Open ${SERVICE_URL} in your browser."
