#!/usr/bin/env bash
set -e

# ==============================================================================
# NZZ FlexRead - 1-Click GCP Cloud Run Deployment Script (English Edition)
# ==============================================================================

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GOOGLE_CLOUD_LOCATION:-europe-west1}"
SERVICE_NAME="nzz-flexread-backend"
REPO_NAME="nzz-flexread"

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: No GCP Project specified."
    echo "Please set GOOGLE_CLOUD_PROJECT or run: gcloud config set project <PROJECT_ID>"
    exit 1
fi

echo "============================================================"
echo "Deploying NZZ FlexRead Backend to Google Cloud Platform"
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Service:  $SERVICE_NAME"
echo "============================================================"

# 1. Enable required GCP services
echo "Enabling GCP APIs (Cloud Run, Artifact Registry, Vertex AI, Cloud Build)..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    cloudbuild.googleapis.com \
    --project="$PROJECT_ID"

# 2. Ensure Artifact Registry repository exists
echo "Checking Artifact Registry repository '$REPO_NAME'..."
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Creating Docker repository '$REPO_NAME' in '$REGION'..."
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="NZZ FlexRead Docker repository" \
        --project="$PROJECT_ID"
fi

IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest"

# 3. Build container using Cloud Build
echo "Building container image using Cloud Build ($IMAGE_TAG)..."
gcloud builds submit \
    --project="$PROJECT_ID" \
    --tag="$IMAGE_TAG" \
    --file=backend/Dockerfile \
    .

# 4. Deploy to Cloud Run with Vertex AI integration
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_TAG" \
    --platform="managed" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --set-env-vars="ENV=production,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GEMINI_MODEL=gemini-2.5-flash,CACHE_TYPE=sqlite"

echo "============================================================"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")
echo "Deployment successful!"
echo "Service URL: $SERVICE_URL"
echo "Health Check: $SERVICE_URL/health"
echo "API Docs:     $SERVICE_URL/docs"
echo "============================================================"
