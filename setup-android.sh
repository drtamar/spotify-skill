#!/usr/bin/env bash
# Spotify Skill — setup for Android via Termux
# Install Termux from https://f-droid.org/packages/com.termux/ (NOT Google Play)
set -e

echo ""
echo "=== Spotify Skill Setup (Android / Termux) ==="
echo ""

# Update Termux packages
echo "Updating packages..."
pkg update -y -q
pkg upgrade -y -q

# Install required system packages
echo "Installing system dependencies..."
pkg install -y -q python python-pip openssl libxml2 libxslt

# cairosvg needs cairo — install via pkg
pkg install -y -q cairo pkg-config

echo "Done."

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --quiet requests python-dotenv pillow
# cairosvg needs special handling on Termux
pip install --quiet cairosvg || echo "Note: cairosvg install failed — cover art generation may be limited on Android."

# Create .env if missing
ENV_FILE="spotify-api/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp spotify-api/.env.example "$ENV_FILE"
    echo ""
    echo "Created $ENV_FILE from template."
fi

# Prompt for credentials
if grep -q "your_client_id_here" "$ENV_FILE"; then
    echo ""
    echo "Enter your Spotify credentials (from https://developer.spotify.com/dashboard):"
    echo ""
    read -rp "  Client ID:     " CLIENT_ID
    read -rp "  Client Secret: " CLIENT_SECRET

    sed -i "s/your_client_id_here/$CLIENT_ID/" "$ENV_FILE"
    sed -i "s/your_client_secret_here/$CLIENT_SECRET/" "$ENV_FILE"
    echo ""
    echo "Credentials saved."
fi

# Generate refresh token
if grep -q "your_refresh_token_here" "$ENV_FILE"; then
    echo ""
    echo "Generating refresh token..."
    echo "A URL will appear — open it in your Android browser, log in, then paste the redirect URL back here."
    echo ""
    python get_refresh_token.py
fi

# Validate
echo ""
echo "Validating credentials..."
python spotify-api/scripts/test_credentials.py

echo ""
echo "=== Setup complete! Run skills with: python spotify-api/scripts/<script>.py ==="
echo ""
