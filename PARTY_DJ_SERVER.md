# party_dj_server.py

**Location:** `spotify-api/scripts/party_dj_server.py`

Social Party DJ web server. Guests scan a QR code and control music from their phone browser — no app install needed.

---

## Quick Start

```bash
# Local (Android/Termux or Mac/Linux)
python party_dj_server.py

# With options
python party_dj_server.py --skip-votes 3 --crossfade 8 --port 5000

# Cloud Run (deployed via deploy-cloud.sh)
# Accessed at https://dj.elama.top
```

---

## Features

| Feature | How it works |
|---|---|
| **Now Playing** | Shows current track, album art, live progress bar |
| **Blurred background** | Full-screen album art, crossfades on track change |
| **Skip voting** | Guests vote — auto-skips when threshold reached |
| **Remix toggle** | Switches search to find remixes & extended versions |
| **Song suggestions** | Search Spotify → add directly to queue |
| **Suggestion queue** | Shows last 8 suggestions in order |

---

## Arguments

| Flag | Default | Description |
|---|---|---|
| `--port` | `5000` | Port to run on |
| `--skip-votes` | `3` | Votes needed to skip a song |
| `--crossfade` | `8` | Crossfade animation duration (seconds) |

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Guest web UI |
| `GET` | `/api/now` | Current track, vote count, suggestions |
| `POST` | `/api/skip` | Cast a skip vote |
| `GET` | `/api/search?q=&remix=` | Search Spotify tracks |
| `POST` | `/api/suggest` | Add a track to the queue |

---

## Credential Loading (priority order)

1. **Environment variables** — used in Cloud Run (`SPOTIFY_CLIENT_ID` etc.)
2. **`spotify-api/.env`** — plaintext, local development
3. **`spotify-api/.env.encrypted`** — encrypted, prompts for password

---

## Dependencies

```
flask>=3.0.0       # web server
qrcode>=7.4.2      # QR code in terminal (optional)
requests           # Spotify API calls (via spotify_client.py)
python-dotenv      # .env loading
gunicorn           # production server (Cloud Run)
```

Install:
```bash
pip install -r spotify-api/requirements.txt
```

---

## Running on Android (Termux)

```bash
pkg install python python-pip -y
pip install flask requests python-dotenv qrcode
cd ~/spotify-skill
python spotify-api/scripts/party_dj_server.py
```

A QR code prints in the terminal. Guests on the same WiFi scan it and open the DJ page.

---

## Deploying to Cloud (Google Cloud Run)

```bash
./deploy-cloud.sh
```

- Project: `tams-parties`
- URL: `https://dj.elama.top`
- DNS: `CNAME dj → ghs.googlehosted.com.`

See [`deploy-cloud.sh`](deploy-cloud.sh) for full deployment details.

---

## Environment Variables (Cloud Run)

| Variable | Required | Description |
|---|---|---|
| `SPOTIFY_CLIENT_ID` | ✅ | Spotify app client ID |
| `SPOTIFY_CLIENT_SECRET` | ✅ | Spotify app client secret |
| `SPOTIFY_REFRESH_TOKEN` | ✅ | OAuth refresh token |
| `SPOTIFY_REDIRECT_URI` | ✅ | `https://dj.elama.top/callback` |
| `SKIP_VOTES` | optional | Override skip threshold |
| `CROSSFADE` | optional | Override crossfade seconds |
| `DJ_PASSWORD` | optional | Skip password prompt for encrypted credentials |

---

## How the Skip Works

1. Guest taps **⏭ Vote to Skip**
2. Their IP is recorded — one vote per device
3. Progress bar fills as votes accumulate
4. When votes reach threshold → `POST /me/player/next` fires
5. Votes reset automatically when the track changes

---

## Project Structure

```
spotify-skill/
├── Dockerfile                          # Cloud Run container
├── deploy-cloud.sh                     # One-command deploy to GCP
├── PARTY_DJ_SERVER.md                  # This file
├── spotify-api/
│   ├── credentials.py                  # Encryption/decryption
│   ├── .env                            # Local credentials (git-ignored)
│   ├── .env.encrypted                  # Encrypted credentials (safe to commit)
│   ├── requirements.txt
│   └── scripts/
│       ├── party_dj_server.py          # ← This file
│       └── spotify_client.py           # Spotify API wrapper
└── .github/workflows/
    └── deploy.yml                      # Auto-deploy on push to main
```
