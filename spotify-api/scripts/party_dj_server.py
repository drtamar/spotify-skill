"""
Party DJ Server — Social skip voting + song suggestions over local WiFi.

Guests scan a QR code → mobile web page → vote to skip or suggest songs.
Run this on the DJ phone via Termux.

Usage:
    python party_dj_server.py
    python party_dj_server.py --skip-votes 3 --port 5000
"""

import argparse
import os
import socket
import sys
import threading
import time
from pathlib import Path

# Add parent dir so spotify_client is importable
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request, render_template_string
from spotify_client import SpotifyClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

app = Flask(__name__)

# ── State ──────────────────────────────────────────────────────────────────────

skip_votes: set = set()          # set of voter IPs
suggestions: list = []           # [{track_uri, name, artist, added_by}]
last_track_id: str = ""          # detect track changes to reset votes
SKIP_THRESHOLD: int = 3          # votes needed to skip

spotify: SpotifyClient = None

# ── Spotify helpers ────────────────────────────────────────────────────────────

def get_client() -> SpotifyClient:
    global spotify
    if spotify is None:
        spotify = SpotifyClient(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
            refresh_token=os.getenv("SPOTIFY_REFRESH_TOKEN"),
        )
    return spotify


def add_to_queue(track_uri: str) -> None:
    client = get_client()
    client._make_request("POST", "me/player/queue", params={"uri": track_uri})


def current_track() -> dict:
    try:
        data = get_client().get_currently_playing()
        if not data or data.get("currently_playing_type") != "track":
            return {}
        item = data.get("item", {})
        return {
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
            "album_art": (item.get("album", {}).get("images") or [{}])[0].get("url", ""),
            "progress_ms": data.get("progress_ms", 0),
            "duration_ms": item.get("duration_ms", 1),
            "is_playing": data.get("is_playing", False),
        }
    except Exception:
        return {}


# Reset skip votes whenever the track changes
def track_watcher():
    global last_track_id, skip_votes
    while True:
        try:
            track = current_track()
            tid = track.get("id", "")
            if tid and tid != last_track_id:
                last_track_id = tid
                skip_votes = set()
        except Exception:
            pass
        time.sleep(5)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/now")
def api_now():
    track = current_track()
    track["skip_votes"] = len(skip_votes)
    track["skip_threshold"] = SKIP_THRESHOLD
    track["my_vote"] = request.remote_addr in skip_votes
    track["suggestions"] = suggestions[-10:]  # last 10
    return jsonify(track)


@app.route("/api/skip", methods=["POST"])
def api_skip():
    global skip_votes
    ip = request.remote_addr
    if ip in skip_votes:
        return jsonify({"ok": False, "msg": "Already voted"})

    skip_votes.add(ip)
    count = len(skip_votes)

    if count >= SKIP_THRESHOLD:
        try:
            get_client().next_track()
            skip_votes = set()
            return jsonify({"ok": True, "skipped": True, "votes": count})
        except Exception as e:
            return jsonify({"ok": False, "msg": str(e)})

    return jsonify({"ok": True, "skipped": False, "votes": count, "needed": SKIP_THRESHOLD})


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    try:
        results = get_client().search_tracks(q, limit=8)
        return jsonify([
            {
                "uri": t["uri"],
                "name": t["name"],
                "artist": ", ".join(a["name"] for a in t.get("artists", [])),
                "album_art": (t.get("album", {}).get("images") or [{}])[-1].get("url", ""),
            }
            for t in results
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/suggest", methods=["POST"])
def api_suggest():
    data = request.json or {}
    uri = data.get("uri", "")
    name = data.get("name", "")
    artist = data.get("artist", "")
    if not uri:
        return jsonify({"ok": False, "msg": "No track URI"})
    try:
        add_to_queue(uri)
        suggestions.append({"name": name, "artist": artist, "uri": uri})
        if len(suggestions) > 50:
            suggestions.pop(0)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


# ── HTML (mobile-first, embedded) ──────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Party DJ</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0a0a0a;
    color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    min-height: 100vh;
    padding: 16px;
  }
  h1 { font-size: 1.1rem; text-align: center; color: #1DB954; margin-bottom: 16px; letter-spacing: 2px; text-transform: uppercase; }

  /* Now playing */
  #now-playing {
    display: flex; gap: 12px; align-items: center;
    background: #1a1a1a; border-radius: 12px; padding: 12px; margin-bottom: 16px;
  }
  #album-art { width: 64px; height: 64px; border-radius: 8px; object-fit: cover; background: #333; flex-shrink: 0; }
  #track-info { flex: 1; overflow: hidden; }
  #track-name { font-size: 1rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  #track-artist { font-size: 0.85rem; color: #aaa; margin-top: 2px; }
  #progress-bar { height: 3px; background: #333; border-radius: 2px; margin-top: 8px; }
  #progress-fill { height: 100%; background: #1DB954; border-radius: 2px; transition: width 1s linear; }

  /* Skip button */
  #skip-section { text-align: center; margin-bottom: 20px; }
  #skip-btn {
    background: #e63946; color: #fff; border: none; border-radius: 50px;
    padding: 14px 40px; font-size: 1.1rem; font-weight: 700; cursor: pointer;
    width: 100%; max-width: 300px; transition: background 0.2s, transform 0.1s;
    letter-spacing: 1px;
  }
  #skip-btn:active { transform: scale(0.97); }
  #skip-btn:disabled { background: #555; cursor: default; }
  #skip-btn.voted { background: #c1121f; }
  #vote-count { margin-top: 8px; font-size: 0.85rem; color: #aaa; }

  /* Search */
  #suggest-section { background: #1a1a1a; border-radius: 12px; padding: 14px; }
  #suggest-section h2 { font-size: 0.95rem; margin-bottom: 10px; color: #1DB954; text-transform: uppercase; letter-spacing: 1px; }
  #search-input {
    width: 100%; padding: 10px 14px; border-radius: 8px;
    border: 1px solid #333; background: #111; color: #fff;
    font-size: 0.95rem; outline: none;
  }
  #search-input:focus { border-color: #1DB954; }
  #results { margin-top: 10px; }
  .result-item {
    display: flex; align-items: center; gap: 10px;
    padding: 8px; border-radius: 8px; cursor: pointer; transition: background 0.15s;
  }
  .result-item:hover, .result-item:active { background: #2a2a2a; }
  .result-thumb { width: 40px; height: 40px; border-radius: 4px; object-fit: cover; background: #333; flex-shrink: 0; }
  .result-info { flex: 1; overflow: hidden; }
  .result-name { font-size: 0.9rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .result-artist { font-size: 0.78rem; color: #aaa; }
  .add-btn {
    background: #1DB954; color: #000; border: none; border-radius: 20px;
    padding: 6px 14px; font-size: 0.8rem; font-weight: 700; cursor: pointer; flex-shrink: 0;
  }
  .add-btn.added { background: #555; color: #aaa; cursor: default; }

  /* Queue */
  #queue-section { margin-top: 16px; }
  #queue-section h2 { font-size: 0.85rem; color: #555; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  .queue-item { font-size: 0.82rem; color: #777; padding: 3px 0; border-bottom: 1px solid #1a1a1a; }
  .queue-item span { color: #aaa; }

  #toast {
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    background: #1DB954; color: #000; padding: 10px 20px; border-radius: 20px;
    font-weight: 700; font-size: 0.9rem; opacity: 0; transition: opacity 0.3s;
    pointer-events: none; white-space: nowrap;
  }
  #toast.show { opacity: 1; }
</style>
</head>
<body>
<h1>🎶 Party DJ</h1>

<div id="now-playing">
  <img id="album-art" src="" alt="">
  <div id="track-info">
    <div id="track-name">Loading...</div>
    <div id="track-artist"></div>
    <div id="progress-bar"><div id="progress-fill" style="width:0%"></div></div>
  </div>
</div>

<div id="skip-section">
  <button id="skip-btn" onclick="vote()">⏭ SKIP THIS SONG</button>
  <div id="vote-count"></div>
</div>

<div id="suggest-section">
  <h2>🎵 Suggest a Song</h2>
  <input id="search-input" type="search" placeholder="Search artist, song..." autocomplete="off" oninput="debounceSearch(this.value)">
  <div id="results"></div>
</div>

<div id="queue-section">
  <h2>Suggested Queue</h2>
  <div id="queue-list"></div>
</div>

<div id="toast"></div>

<script>
let myVoted = false;
let debounceTimer = null;

function toast(msg, color) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = color || '#1DB954';
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

async function refresh() {
  try {
    const r = await fetch('/api/now');
    const d = await r.json();
    if (!d.name) return;

    document.getElementById('track-name').textContent = d.name;
    document.getElementById('track-artist').textContent = d.artist;
    const art = document.getElementById('album-art');
    if (d.album_art && art.src !== d.album_art) art.src = d.album_art;

    const pct = d.duration_ms ? Math.round(d.progress_ms / d.duration_ms * 100) : 0;
    document.getElementById('progress-fill').style.width = pct + '%';

    myVoted = d.my_vote;
    const btn = document.getElementById('skip-btn');
    btn.disabled = myVoted;
    btn.classList.toggle('voted', myVoted);
    const needed = d.skip_threshold - d.skip_votes;
    document.getElementById('vote-count').textContent =
      myVoted ? `You voted — ${needed} more vote${needed !== 1 ? 's' : ''} to skip`
              : `${d.skip_votes} / ${d.skip_threshold} votes to skip`;

    // Queue
    const ql = document.getElementById('queue-list');
    ql.innerHTML = (d.suggestions || []).slice().reverse().map(s =>
      `<div class="queue-item"><span>${s.name}</span> — ${s.artist}</div>`
    ).join('') || '<div class="queue-item" style="color:#444">None yet</div>';
  } catch(e) {}
}

async function vote() {
  const btn = document.getElementById('skip-btn');
  btn.disabled = true;
  try {
    const r = await fetch('/api/skip', {method:'POST'});
    const d = await r.json();
    if (d.skipped) {
      toast('⏭ Song skipped!', '#1DB954');
    } else if (d.ok) {
      toast(`Vote counted! ${d.votes}/${d.needed} to skip`, '#f4a261');
    } else {
      toast(d.msg || 'Error', '#e63946');
      btn.disabled = false;
    }
    refresh();
  } catch(e) { btn.disabled = false; }
}

function debounceSearch(q) {
  clearTimeout(debounceTimer);
  if (!q.trim()) { document.getElementById('results').innerHTML = ''; return; }
  debounceTimer = setTimeout(() => search(q), 500);
}

async function search(q) {
  try {
    const r = await fetch('/api/search?q=' + encodeURIComponent(q));
    const tracks = await r.json();
    const el = document.getElementById('results');
    if (!Array.isArray(tracks)) { el.innerHTML = ''; return; }
    el.innerHTML = tracks.map(t => `
      <div class="result-item">
        <img class="result-thumb" src="${t.album_art}" onerror="this.src=''">
        <div class="result-info">
          <div class="result-name">${t.name}</div>
          <div class="result-artist">${t.artist}</div>
        </div>
        <button class="add-btn" onclick="suggest('${t.uri}','${t.name.replace(/'/g,"\\'")}','${t.artist.replace(/'/g,"\\'")}',this)">+ Add</button>
      </div>`).join('');
  } catch(e) {}
}

async function suggest(uri, name, artist, btn) {
  btn.disabled = true;
  btn.classList.add('added');
  btn.textContent = '✓';
  try {
    const r = await fetch('/api/suggest', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({uri, name, artist})
    });
    const d = await r.json();
    if (d.ok) {
      toast('🎵 Added to queue!', '#1DB954');
      document.getElementById('search-input').value = '';
      document.getElementById('results').innerHTML = '';
      refresh();
    } else {
      toast(d.msg || 'Error', '#e63946');
      btn.disabled = false; btn.classList.remove('added'); btn.textContent = '+ Add';
    }
  } catch(e) { btn.disabled = false; btn.classList.remove('added'); btn.textContent = '+ Add'; }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""


# ── QR code ────────────────────────────────────────────────────────────────────

def print_qr(url: str):
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        pass  # qrcode optional


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Party DJ Server")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--skip-votes", type=int, default=3, dest="skip_votes")
    args = parser.parse_args()

    SKIP_THRESHOLD = args.skip_votes

    ip = get_local_ip()
    url = f"http://{ip}:{args.port}"

    print(f"\n🎶  Party DJ Server starting...")
    print(f"📱  Guests open: {url}")
    print(f"⏭   Skip threshold: {SKIP_THRESHOLD} votes")
    print(f"\nScan this QR code to join:\n")
    print_qr(url)
    print(f"\nPress Ctrl+C to stop.\n")

    threading.Thread(target=track_watcher, daemon=True).start()
    app.run(host="0.0.0.0", port=args.port, debug=False)
