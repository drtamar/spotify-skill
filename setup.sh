#!/usr/bin/env bash
# Spotify Skill — one-command setup for Mac/Linux
set -e

echo ""
echo "=== Spotify Skill Setup ==="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3.8+ is required. Install from https://python.org"
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python $PY_VER detected."

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt --quiet
pip3 install -r spotify-api/requirements.txt --quiet
echo "Done."

# Create .env if missing
ENV_FILE="spotify-api/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp spotify-api/.env.example "$ENV_FILE"
    echo ""
    echo "Created $ENV_FILE from template."
fi

# Prompt for credentials if placeholders still present
if grep -q "your_client_id_here" "$ENV_FILE"; then
    echo ""
    echo "Enter your Spotify credentials (from https://developer.spotify.com/dashboard):"
    echo ""
    read -rp "  Client ID:     " CLIENT_ID
    read -rp "  Client Secret: " CLIENT_SECRET

    sed -i.bak "s/your_client_id_here/$CLIENT_ID/" "$ENV_FILE"
    sed -i.bak "s/your_client_secret_here/$CLIENT_SECRET/" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
    echo ""
    echo "Credentials saved to $ENV_FILE"
fi

# Generate refresh token if missing
if grep -q "your_refresh_token_here" "$ENV_FILE"; then
    echo ""
    echo "Now generating your Spotify refresh token..."
    echo "(A browser window will open — log in and authorize the app)"
    echo ""
    python3 get_refresh_token.py
fi

# Validate
echo ""
echo "Validating credentials..."
python3 spotify-api/scripts/test_credentials.py

echo ""
echo "=== Setup complete! The Spotify Skill is ready to use. ==="
echo ""
