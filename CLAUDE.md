# CLAUDE.md — Party DJ Project State

**Last updated:** 2026-05-29  
**Project:** Funky Day Party Autonomous DJ  
**Repo:** drtamar/spotify-skill  
**User:** Tam (Israel) — tam.savt@gmail.com

---

## What This Project Is

Social Party DJ web app for small day parties (5–50 people, 10–12 hours).  
Old Android phone plays Spotify → guests scan QR code → vote to skip songs, suggest tracks.  
Hosted at `https://dj.elama.top` on Google Cloud Run (project: `tams-parties`).

Long-term vision: phone watches the dance floor with its camera, detects when energy drops,
auto-skips to higher-energy tracks. MVP uses skip voting. Camera automation comes later.

---

## Current Status

### Done
- `spotify-api/scripts/party_dj_server.py` — full Flask web app (now-playing, skip voting, remix search, suggestion queue, blurred album art, crossfade UI)
- `spotify-api/credentials.py` — zero-dependency credential encryption (PBKDF2 + HMAC-SHA256, stdlib only)
- `Dockerfile` — Cloud Run container
- `deploy-cloud.sh` — one-command deploy to GCP
- `.github/workflows/deploy.yml` — auto-deploy on push to `main`
- `PARTY_DJ_SERVER.md` — full documentation
- `get_token_manual.py` — paste-method OAuth token generator (no local server needed)
- DNS configured: `dj.elama.top` CNAME → `ghs.googlehosted.com.` (Namecheap)
- PR #4 open: `claude/fix-jetbrains-review-feedback` → `main` (draft, ready to merge)

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
SPOTIFY_REFRESH_TOKEN=<pending — user knows how to get it>
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

Script prints auth URL → user clicks Agree on Spotify → copies redirect URL from browser
address bar → pastes back → script exchanges the code and prints the refresh token.

**Important:** Add the Cloud Shell callback URL to Spotify Dashboard first:
`https://8888-cs-587211722978-default.cs-europe-west4-fycr.cloudshell.dev/callback`

Note: Cloud Shell preview URL changes each session — update `SPOTIFY_REDIRECT_URI` and
Spotify Dashboard if the URL is different.

---

## Deployment

### Via GitHub Actions (recommended)
Set these secrets in repo Settings → Secrets → Actions:
- `GCP_SA_KEY` — Google Cloud service account JSON key
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REFRESH_TOKEN`

Then merge PR #4. Auto-deploys to `https://dj.elama.top`.

### Manual (Cloud Shell or local)
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

Music style: groovy, funky, ass-moving, bass-heavy — NOT dark techno/aggression.
Day-party friendly. Sunny, sexy, danceable.

### Phase 1 Tracks (Warm-Up)
Ganga Giri, Ash Dargan, TJ Rehmi, Quantic Soul Orchestra, St Germain – Rose Rouge,
Thievery Corporation – Lebanese Blonde, Bonobo – Kerala, Emapea – Mind,
Nickodemus – Sun People, Fat Freddy's Drop – Roady, Khruangbin – Time (You and I),
Lane 8 – Road, Desert Dwellers – Wandering Sadhu, Porangui – Medicina

### Phase 2 Tracks (Build)
Chronixx – Here Comes Trouble, Protoje – Resist Not, Kabaka Pyramid – Well Done,
Busy Signal – Night Shift, Vybz Kartel – Fever, Major Lazer – Pon de Floor,
Damian Marley – Welcome to Jamrock, Sister Nancy – Bam Bam,
Burna Boy – Ye, Wizkid – Essence, Sean Paul – Temperature

### Phase 3 Tracks (Peak)
Peggy Gou – Nanana, Michael Bibi – Hanging Tree, Bontan – Call You Back,
Black Coffee – Turn Me On, Anderson .Paak – Come Down, Kaytranada – You're the One,
Dom Dolla – Take It, Chris Lake – Turn Off The Lights, Fisher – Losing It,
Silk Sonic – Leave the Door Open, Dua Lipa – Don't Start Now (funky remix)

### Phase 4 Tracks (Wind Down)
FKJ – Vibin', Jordan Rakei – Mind's Eye, Tom Misch – Lost in Paris,
Hiatus Kaiyote – Breathing Underwater, Khruangbin – August 10,
ODESZA – A Moment Apart, Rufus Du Sol – Underwater,
Bonobo – Migration, Thievery Corporation – The Richest Man in Babylon,
Emancipator – First Snow, Porangui – Cura

---

## Key Files

```
spotify-skill/
├── CLAUDE.md                               ← this file
├── PARTY_DJ_SERVER.md                      ← Party DJ documentation
├── Dockerfile                              ← Cloud Run container
├── deploy-cloud.sh                         ← one-command GCP deploy
├── get_refresh_token.py                    ← original (needs local server)
├── get_token_manual.py                     ← paste method, no server needed ✓
├── .github/workflows/deploy.yml            ← auto-deploy on push to main
└── spotify-api/
    ├── credentials.py                      ← encryption/decryption (stdlib only)
    ├── .env                                ← local credentials (git-ignored)
    ├── .env.encrypted                      ← encrypted backup (password: partydjsecret)
    ├── requirements.txt
    └── scripts/
        ├── party_dj_server.py              ← THE app
        └── spotify_client.py               ← Spotify API wrapper
```

---

## Known Issues / Environment Notes

- Git pushes from Claude Code session go through a local proxy (`127.0.0.1:PORT`) — returns 403. Use GitHub web UI or push from your own machine.
- `cryptography` pip package broken on dev machine — `credentials.py` uses stdlib only (no external deps).
- Cloud Shell Web Preview URL changes each session — update `SPOTIFY_REDIRECT_URI` and Spotify Dashboard accordingly.
- GCP IAM permissions already fixed: Cloud Build service account has `roles/run.admin` and `roles/iam.serviceAccountUser`.

---

## Immediate Next Steps

1. Get Spotify refresh token (`python get_token_manual.py`)
2. Set 4 GitHub secrets (GCP_SA_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN)
3. Merge PR #4 → auto-deploys → `https://dj.elama.top` goes live
4. Test: scan QR code, vote to skip, suggest a song

## Future (after launch)
- Mount phone camera at dance floor
- Add IP Webcam + Tasker: detect low movement → auto-skip
- Visual energy detection for fully autonomous DJ
