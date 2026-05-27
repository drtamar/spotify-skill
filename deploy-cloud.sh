#!/usr/bin/env bash
# Deploy Party DJ to Google Cloud Run with custom subdomain
#
# Prerequisites:
#   1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
#   2. Run: gcloud auth login
#   3. Run: gcloud config set project YOUR_PROJECT_ID
#   4. Have your Spotify credentials ready
#
# Usage:
#   ./deploy-cloud.sh
#   ./deploy-cloud.sh --subdomain dj.yourdomain.com --skip-votes 3

set -e

# ── Config ─────────────────────────────────────────────────────────────────────
SERVICE_NAME="party-dj"
REGION="us-central1"          # change to region nearest your guests
SUBDOMAIN=""
SKIP_VOTES=3
CROSSFADE=8

while [[ $# -gt 0 ]]; do
  case $1 in
    --subdomain) SUBDOMAIN="$2"; shift 2 ;;
    --skip-votes) SKIP_VOTES="$2"; shift 2 ;;
    --crossfade) CROSSFADE="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# ── Detect project ─────────────────────────────────────────────────────────────
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT" ]; then
  echo "ERROR: No GCloud project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi
IMAGE="gcr.io/$PROJECT/$SERVICE_NAME"

echo ""
echo "=== Party DJ → Google Cloud Run ==="
echo "Project : $PROJECT"
echo "Region  : $REGION"
echo "Image   : $IMAGE"
echo ""

# ── Read Spotify credentials ───────────────────────────────────────────────────
ENV_FILE="spotify-api/.env"
if [ -f "$ENV_FILE" ]; then
  source "$ENV_FILE" 2>/dev/null || true
fi

if [ -z "$SPOTIFY_CLIENT_ID" ]; then
  read -rp "Spotify Client ID:     " SPOTIFY_CLIENT_ID
fi
if [ -z "$SPOTIFY_CLIENT_SECRET" ]; then
  read -rp "Spotify Client Secret: " SPOTIFY_CLIENT_SECRET
fi
if [ -z "$SPOTIFY_REFRESH_TOKEN" ]; then
  echo ""
  echo "You need a refresh token. Run locally first: python get_refresh_token.py"
  read -rp "Spotify Refresh Token: " SPOTIFY_REFRESH_TOKEN
fi

# Redirect URI for cloud — use service URL or custom subdomain
if [ -n "$SUBDOMAIN" ]; then
  REDIRECT_URI="https://$SUBDOMAIN/callback"
else
  # We'll update after first deploy
  REDIRECT_URI="http://127.0.0.1:8888/callback"
fi

# ── Enable required APIs ───────────────────────────────────────────────────────
echo "Enabling Cloud APIs..."
gcloud services enable run.googleapis.com containerregistry.googleapis.com \
  cloudbuild.googleapis.com --quiet

# ── Build & push image ─────────────────────────────────────────────────────────
echo ""
echo "Building Docker image..."
gcloud builds submit --tag "$IMAGE" --quiet .

# ── Deploy to Cloud Run ────────────────────────────────────────────────────────
echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "SPOTIFY_CLIENT_ID=$SPOTIFY_CLIENT_ID,SPOTIFY_CLIENT_SECRET=$SPOTIFY_CLIENT_SECRET,SPOTIFY_REFRESH_TOKEN=$SPOTIFY_REFRESH_TOKEN,SPOTIFY_REDIRECT_URI=$REDIRECT_URI,SKIP_VOTES=$SKIP_VOTES,CROSSFADE=$CROSSFADE" \
  --min-instances 0 \
  --max-instances 1 \
  --memory 256Mi \
  --quiet

# ── Get service URL ────────────────────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --platform managed --region "$REGION" \
  --format "value(status.url)")

echo ""
echo "=== Deployed! ==="
echo "Service URL: $SERVICE_URL"

# ── Custom subdomain ───────────────────────────────────────────────────────────
if [ -n "$SUBDOMAIN" ]; then
  echo ""
  echo "Mapping custom subdomain: $SUBDOMAIN"
  gcloud run domain-mappings create \
    --service "$SERVICE_NAME" \
    --domain "$SUBDOMAIN" \
    --region "$REGION" \
    --quiet 2>/dev/null || true

  echo ""
  echo "=== DNS Setup Required ==="
  echo "Add this to your DNS provider:"
  echo ""
  gcloud run domain-mappings describe \
    --domain "$SUBDOMAIN" \
    --region "$REGION" \
    --format="value(status.resourceRecords[].rrdata)" 2>/dev/null || \
    echo "  CNAME $SUBDOMAIN → ghs.googlehosted.com."
  echo ""
  echo "=== Spotify Dashboard Update Required ==="
  echo "Add this redirect URI to your Spotify app:"
  echo "  https://$SUBDOMAIN/callback"
  echo ""
  echo "Party DJ live at: https://$SUBDOMAIN"
else
  echo ""
  echo "Party DJ live at: $SERVICE_URL"
  echo ""
  echo "To add a custom subdomain, redeploy with:"
  echo "  ./deploy-cloud.sh --subdomain dj.yourdomain.com"
fi
