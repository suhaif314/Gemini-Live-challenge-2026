#!/bin/bash
# deploy.sh — Automated deployment to Google Cloud Run
# Usage: ./deploy.sh

set -euo pipefail

# ============================================================
# Configuration — Update these variables for your project
# ============================================================
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-gcp-project-id}"
REGION="us-central1"
SERVICE_NAME="live-ai-voice-translator"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

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
echo "[1/6] Enabling required Google Cloud APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    texttospeech.googleapis.com \
    translate.googleapis.com \
    containerregistry.googleapis.com \
    --project="${PROJECT_ID}"
echo "  APIs enabled."

# ============================================================
# Step 2: Set project
# ============================================================
echo "[2/6] Setting active project..."
gcloud config set project "${PROJECT_ID}"

# ============================================================
# Step 3: Build Docker image with Cloud Build
# ============================================================
echo "[3/6] Building container image with Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}" .
echo "  Image built: ${IMAGE_NAME}"

# ============================================================
# Step 4: Deploy to Cloud Run
# ============================================================
echo "[4/6] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8501 \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=5 \
    --set-env-vars="GOOGLE_API_KEY=${GOOGLE_API_KEY:-}" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --timeout=300

echo "  Deployed to Cloud Run."

# ============================================================
# Step 5: Get the service URL
# ============================================================
echo "[5/6] Retrieving service URL..."
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
# Step 6: Verify deployment
# ============================================================
echo "[6/6] Verifying deployment..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/_stcore/health" || echo "000")
if [ "${STATUS_CODE}" = "200" ]; then
    echo "  Health check PASSED (HTTP ${STATUS_CODE})"
else
    echo "  Health check returned HTTP ${STATUS_CODE} (may need a moment to start)"
fi

echo ""
echo "Done! Open ${SERVICE_URL} in your browser."
