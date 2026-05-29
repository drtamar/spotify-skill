# CLAUDE.md — Party DJ Project State

**Last updated:** 2026-05-29  
**Project:** Funky Day Party Autonomous DJ  
**Repo:** drtamar/spotify-skill

---

## What This Project Is

Social Party DJ web app for small day parties (5–50 people, 10–12 hours).  
Old Android phone plays Spotify → guests scan QR code → vote to skip songs, suggest tracks.  
Hosted at `https://dj.elama.top` on Google Cloud Run (project: `tams-parties`).

---

## Current Status

### Done
- `spotify-api/scripts/party_dj_server.py` — full Flask web app (now-playing, skip voting, remix search, suggestion queue, blurred album art, crossfade UI)
- `spotify-api/credentials.py` — zero-dependency credential encryption (PBKDF2 + HMAC-SHA256, stdlib only)
- `Dockerfile` — Cloud Run container
- `deploy-cloud.sh` — one-command deploy to GCP
- `.github/workflows/deploy.yml` — auto-deploy on push to `main`
- `PARTY_DJ_SERVER.md` — full documentation
- DNS configured: `dj.elama.top` CNAME → `ghs.googlehosted.com.` (Namecheap)
- PR #4 open: `claude/fix-jetbrains-review-feedback` → `main` (draft)

### Blocking deployment
- **Spotify refresh token not yet generated** — user said they found how to get it
- **GitHub secrets not set** — need `GCP_SA_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REFRESH_TOKEN`

### Once secrets + token are ready
Merge PR #4 → GitHub Actions deploys automatically → `https://dj.elama.top` goes live.

---

## Credentials (do NOT commit these)

```
SPOTIFY_CLIENT_ID=ac7ad864d57b4bca86144cc02899490d
SPOTIFY_CLIENT_SECRET=01c577abe7cb413fb0ff668a29a9d9ca
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback  (local)
                  or https://dj.elama.top/callback    (production)
SPOTIFY_REFRESH_TOKEN=<pending>
```

Stored locally at `spotify-api/.env` (git-ignored).  
Encrypted backup at `spotify-api/.env.encrypted` (password: `partydjsecret`).

---

## Getting the Refresh Token

Run `get_token_manual.py` — no local server needed, paste method:

```bash
export SPOTIFY_CLIENT_ID=ac7ad864d57b4bca86144cc02899490d
export SPOTIFY_CLIENT_SECRET=01c577abe7cb413fb0ff668a29a9d9ca
export SPOTIFY_REDIRECT_URI=https://8888-cs-587211722978-default.cs-europe-west4-fycr.cloudshell.dev/callback
python get_token_manual.py
```

Script prints auth URL → user clicks Agree on Spotify → copies redirect URL from browser address bar → pastes back → done.

Add the Cloud Shell callback URL to Spotify Dashboard first:  
`https://8888-cs-587211722978-default.cs-europe-west4-fycr.cloudshell.dev/callback`

---

## Deployment

### Via GitHub Actions (recommended — merge PR #4)
Set these secrets in repo Settings → Secrets → Actions:
- `GCP_SA_KEY` — Google Cloud service account JSON key
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REFRESH_TOKEN`

Then merge PR #4. Auto-deploys to `https://dj.elama.top`.

### Manual (Cloud Shell)
```bash
cd ~/spotify-skill
./deploy-cloud.sh
```

---

## Party Structure (4-Phase Journey)

| Phase | Vibe | Duration |
|---|---|---|
| Warm-Up | Tribal, didgeridoo, organic percussion | 2–3 hrs |
| Build | Funky dancehall, modern reggae, groovy bass | 2–3 hrs |
| Peak | Afro-house, reggaeton, funk, hip-hop grooves | 3–4 hrs |
| Wind Down | Deep, melodic, psychedelic, breathable | 2–3 hrs |

Full playlist in `fbe61643-funkydaypartyjourney.md` (uploaded to session).

---

## Key Files

```
spotify-skill/
├── CLAUDE.md                               ← this file
├── PARTY_DJ_SERVER.md                      ← Party DJ documentation
├── Dockerfile                              ← Cloud Run container
├── deploy-cloud.sh                         ← one-command GCP deploy
├── get_refresh_token.py                    ← original (needs server running)
├── get_token_manual.py                     ← paste method, no server needed
├── .github/workflows/deploy.yml            ← auto-deploy on push to main
└── spotify-api/
    ├── credentials.py                      ← encryption/decryption
    ├── .env                                ← local credentials (git-ignored)
    ├── .env.encrypted                      ← encrypted backup
    ├── requirements.txt
    └── scripts/
        ├── party_dj_server.py              ← THE app
        └── spotify_client.py               ← Spotify API wrapper
```

---

## Known Issues / Environment Notes

- Git pushes from this Claude Code session go through a local proxy (`127.0.0.1:PORT`) — sometimes returns 403. If push fails, retry or use GitHub MCP tools.
- `cryptography` pip package broken on dev machine — `credentials.py` uses stdlib only (no external deps).
- Cloud Shell Web Preview URL changes each session — update `SPOTIFY_REDIRECT_URI` and Spotify Dashboard accordingly.
