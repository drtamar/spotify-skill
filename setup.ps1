# Spotify Skill — one-command setup for Windows (PowerShell)

Write-Host ""
Write-Host "=== Spotify Skill Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python 3.8+ is required. Install from https://python.org" -ForegroundColor Red
    exit 1
}

$pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Python $pyVer detected."

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..."
python -m pip install -r requirements.txt --quiet
python -m pip install -r spotify-api/requirements.txt --quiet
Write-Host "Done."

# Create .env if missing
$envFile = "spotify-api\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item "spotify-api\.env.example" $envFile
    Write-Host ""
    Write-Host "Created $envFile from template."
}

# Prompt for credentials if placeholders still present
$envContent = Get-Content $envFile -Raw
if ($envContent -match "your_client_id_here") {
    Write-Host ""
    Write-Host "Enter your Spotify credentials (from https://developer.spotify.com/dashboard):"
    Write-Host ""
    $clientId = Read-Host "  Client ID"
    $clientSecret = Read-Host "  Client Secret"

    (Get-Content $envFile) -replace "your_client_id_here", $clientId `
                           -replace "your_client_secret_here", $clientSecret |
        Set-Content $envFile
    Write-Host ""
    Write-Host "Credentials saved to $envFile"
}

# Generate refresh token if missing
$envContent = Get-Content $envFile -Raw
if ($envContent -match "your_refresh_token_here") {
    Write-Host ""
    Write-Host "Now generating your Spotify refresh token..."
    Write-Host "(A browser window will open — log in and authorize the app)"
    Write-Host ""
    python get_refresh_token.py
}

# Validate
Write-Host ""
Write-Host "Validating credentials..."
python spotify-api/scripts/test_credentials.py

Write-Host ""
Write-Host "=== Setup complete! The Spotify Skill is ready to use. ===" -ForegroundColor Green
Write-Host ""
