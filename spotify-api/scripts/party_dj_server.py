"""
Party DJ Server — Social skip voting, song suggestions, remix search, crossfade.

Usage:
    python party_dj_server.py
    python party_dj_server.py --skip-votes 3 --port 5000 --crossfade 8
"""

import argparse
import os
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, request, render_template_string
from spotify_client import SpotifyClient
from credentials import load_credentials

load_credentials()

app = Flask(__name__)

# ── State ──────────────────────────────────────────────────────────────────────

skip_votes: set = set()
suggestions: list = []
last_track_id: str = ""
SKIP_THRESHOLD: int = 3
CROSSFADE_SECONDS: int = 8

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
    get_client()._make_request("POST", "me/player/queue", params={"uri": track_uri})


def set_crossfade(seconds: int) -> None:
    # Spotify crossfade is a client-side setting; we fade manually via volume
    pass


def current_track() -> dict:
    try:
        data = get_client().get_currently_playing()
        if not data or data.get("currently_playing_type") != "track":
            return {}
        item = data.get("item", {})
        images = item.get("album", {}).get("images") or [{}]
        return {
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
            "album": item.get("album", {}).get("name", ""),
            "album_art": images[0].get("url", ""),
            "album_art_sm": images[-1].get("url", "") if len(images) > 1 else images[0].get("url", ""),
            "progress_ms": data.get("progress_ms", 0),
            "duration_ms": item.get("duration_ms", 1),
            "is_playing": data.get("is_playing", False),
        }
    except Exception:
        return {}


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
        time.sleep(4)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML, crossfade=CROSSFADE_SECONDS)


@app.route("/api/now")
def api_now():
    track = current_track()
    track["skip_votes"] = len(skip_votes)
    track["skip_threshold"] = SKIP_THRESHOLD
    track["my_vote"] = request.remote_addr in skip_votes
    track["suggestions"] = suggestions[-20:]
    track["crossfade"] = CROSSFADE_SECONDS
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
    remix = request.args.get("remix", "false") == "true"
    if not q:
        return jsonify([])
    try:
        query = f"{q} remix" if remix else q
        results = get_client().search_tracks(query, limit=10)
        return jsonify([
            {
                "uri": t["uri"],
                "name": t["name"],
                "artist": ", ".join(a["name"] for a in t.get("artists", [])),
                "duration": _fmt_ms(t.get("duration_ms", 0)),
                "album_art": (t.get("album", {}).get("images") or [{}])[-1].get("url", ""),
                "explicit": t.get("explicit", False),
            }
            for t in results
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/suggest", methods=["POST"])
def api_suggest():
    data = request.json or {}
    uri, name, artist = data.get("uri", ""), data.get("name", ""), data.get("artist", "")
    if not uri:
        return jsonify({"ok": False, "msg": "No track URI"})
    try:
        add_to_queue(uri)
        suggestions.append({"name": name, "artist": artist})
        if len(suggestions) > 50:
            suggestions.pop(0)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


def _fmt_ms(ms: int) -> str:
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


# ── HTML ───────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Party DJ</title>
<style>
  :root {
    --accent: #1DB954;
    --accent2: #ff6b35;
    --bg: #080808;
    --card: rgba(255,255,255,0.06);
    --card-border: rgba(255,255,255,0.1);
    --text: #ffffff;
    --muted: rgba(255,255,255,0.5);
    --crossfade: {{ crossfade }}s;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* ── Background art ── */
  #bg-art {
    position: fixed; inset: -40px;
    background-size: cover; background-position: center;
    filter: blur(60px) brightness(0.3) saturate(1.8);
    transition: background-image var(--crossfade) ease;
    z-index: 0;
  }

  .page { position: relative; z-index: 1; padding: 0 16px 100px; max-width: 480px; margin: 0 auto; }

  /* ── Header ── */
  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 0 8px;
  }
  .logo { font-size: 0.75rem; font-weight: 700; letter-spacing: 3px; color: var(--accent); text-transform: uppercase; }
  .live-dot { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(1.4)} }

  /* ── Now Playing ── */
  #now-playing {
    display: flex; gap: 14px; align-items: center;
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 20px; padding: 16px; margin: 8px 0 16px;
    backdrop-filter: blur(20px);
    transition: all 0.6s ease;
  }
  #album-art {
    width: 72px; height: 72px; border-radius: 12px; object-fit: cover;
    flex-shrink: 0; background: #222;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    transition: all var(--crossfade) ease;
  }
  #album-art.spinning { animation: spin 8s linear infinite; border-radius: 50%; }
  @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
  .track-meta { flex: 1; overflow: hidden; }
  #track-name {
    font-size: 1rem; font-weight: 700;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    transition: opacity 0.4s;
  }
  #track-artist { font-size: 0.82rem; color: var(--muted); margin-top: 2px; }
  #track-album { font-size: 0.75rem; color: var(--muted); margin-top: 1px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* progress */
  .progress-wrap { margin-top: 10px; }
  #progress-bar { height: 3px; background: rgba(255,255,255,0.12); border-radius: 2px; }
  #progress-fill {
    height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent2));
    border-radius: 2px; transition: width 1s linear;
  }
  .time-row { display: flex; justify-content: space-between; font-size: 0.68rem; color: var(--muted); margin-top: 4px; }

  /* ── Skip ── */
  #skip-section { margin-bottom: 16px; }
  .skip-wrap {
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 20px; padding: 16px; backdrop-filter: blur(20px);
  }
  .skip-label { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; }
  #skip-btn {
    width: 100%; padding: 16px; border: none; border-radius: 14px;
    font-size: 1rem; font-weight: 800; letter-spacing: 1px; cursor: pointer;
    background: linear-gradient(135deg, #e63946, #c1121f);
    color: #fff; transition: all 0.2s; text-transform: uppercase;
    box-shadow: 0 4px 20px rgba(230,57,70,0.4);
  }
  #skip-btn:active { transform: scale(0.97); box-shadow: none; }
  #skip-btn:disabled { background: rgba(255,255,255,0.08); color: var(--muted); box-shadow: none; cursor: default; }
  #skip-btn.voted { background: rgba(230,57,70,0.2); border: 1px solid #e63946; color: #e63946; box-shadow: none; }

  /* vote bar */
  .vote-bar-wrap { margin-top: 10px; }
  #vote-bar-bg { height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; }
  #vote-bar-fill { height: 100%; background: #e63946; border-radius: 2px; transition: width 0.4s ease; }
  #vote-text { font-size: 0.75rem; color: var(--muted); margin-top: 5px; text-align: center; }

  /* ── Search & Suggest ── */
  #suggest-section {
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 20px; padding: 16px; margin-bottom: 16px;
    backdrop-filter: blur(20px);
  }
  .section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
  .section-title { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1.5px; }

  /* remix toggle */
  .remix-toggle { display: flex; align-items: center; gap: 6px; cursor: pointer; }
  .remix-toggle span { font-size: 0.72rem; color: var(--muted); }
  .toggle-pill {
    width: 36px; height: 20px; background: rgba(255,255,255,0.1);
    border-radius: 10px; position: relative; transition: background 0.2s; flex-shrink: 0;
  }
  .toggle-pill.on { background: var(--accent); }
  .toggle-pill::after {
    content: ''; position: absolute; top: 3px; left: 3px;
    width: 14px; height: 14px; background: #fff; border-radius: 50%;
    transition: transform 0.2s;
  }
  .toggle-pill.on::after { transform: translateX(16px); }

  /* search input */
  .search-row { display: flex; gap: 8px; }
  #search-input {
    flex: 1; padding: 12px 14px; border-radius: 12px;
    border: 1px solid var(--card-border); background: rgba(255,255,255,0.06);
    color: #fff; font-size: 0.95rem; outline: none;
    transition: border-color 0.2s;
  }
  #search-input:focus { border-color: var(--accent); }
  #search-input::placeholder { color: var(--muted); }

  /* results */
  #results { margin-top: 10px; }
  .result-item {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 6px; border-radius: 10px; cursor: pointer;
    transition: background 0.15s; border-bottom: 1px solid rgba(255,255,255,0.04);
  }
  .result-item:last-child { border-bottom: none; }
  .result-item:active { background: rgba(255,255,255,0.08); }
  .result-thumb {
    width: 44px; height: 44px; border-radius: 8px; object-fit: cover;
    background: #222; flex-shrink: 0;
  }
  .result-info { flex: 1; overflow: hidden; }
  .result-name { font-size: 0.88rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .result-sub { font-size: 0.75rem; color: var(--muted); margin-top: 1px; }
  .result-dur { font-size: 0.72rem; color: var(--muted); flex-shrink: 0; }
  .add-btn {
    background: var(--accent); color: #000; border: none; border-radius: 20px;
    padding: 7px 14px; font-size: 0.78rem; font-weight: 800; cursor: pointer;
    flex-shrink: 0; transition: all 0.2s; letter-spacing: 0.5px;
  }
  .add-btn:active { transform: scale(0.95); }
  .add-btn.added { background: rgba(255,255,255,0.1); color: var(--muted); cursor: default; }

  /* ── Queue ── */
  #queue-section {
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 20px; padding: 16px; backdrop-filter: blur(20px);
  }
  .queue-item {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 0.82rem;
  }
  .queue-item:last-child { border-bottom: none; }
  .queue-num { color: var(--muted); font-size: 0.72rem; width: 16px; flex-shrink: 0; text-align: right; }
  .queue-name { font-weight: 500; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .queue-artist { color: var(--muted); font-size: 0.75rem; white-space: nowrap; }

  /* ── Crossfade indicator ── */
  #crossfade-bar {
    position: fixed; bottom: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    transform: scaleX(0); transform-origin: left;
    transition: transform var(--crossfade) linear;
    z-index: 100;
  }
  #crossfade-bar.fading { transform: scaleX(1); }

  /* ── Toast ── */
  #toast {
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(20px);
    padding: 10px 20px; border-radius: 24px;
    font-weight: 700; font-size: 0.88rem; opacity: 0;
    transition: all 0.3s; pointer-events: none; white-space: nowrap; z-index: 200;
  }
  #toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
</style>
</head>
<body>
<div id="bg-art"></div>
<div id="crossfade-bar"></div>

<div class="page">
  <header>
    <span class="logo">🎶 Party DJ</span>
    <div class="live-dot"></div>
  </header>

  <!-- Now Playing -->
  <div id="now-playing">
    <img id="album-art" src="" alt="">
    <div class="track-meta">
      <div id="track-name">Connecting…</div>
      <div id="track-artist"></div>
      <div id="track-album"></div>
      <div class="progress-wrap">
        <div id="progress-bar"><div id="progress-fill" style="width:0%"></div></div>
        <div class="time-row"><span id="t-now">0:00</span><span id="t-total">0:00</span></div>
      </div>
    </div>
  </div>

  <!-- Skip -->
  <div id="skip-section">
    <div class="skip-wrap">
      <div class="skip-label">Not feeling it?</div>
      <button id="skip-btn" onclick="vote()">⏭  Vote to Skip</button>
      <div class="vote-bar-wrap">
        <div id="vote-bar-bg"><div id="vote-bar-fill" style="width:0%"></div></div>
        <div id="vote-text">Be the first to vote</div>
      </div>
    </div>
  </div>

  <!-- Suggest -->
  <div id="suggest-section">
    <div class="section-header">
      <span class="section-title">🎵 Suggest a Song</span>
      <div class="remix-toggle" onclick="toggleRemix()">
        <span>Remixes</span>
        <div class="toggle-pill" id="remix-pill"></div>
      </div>
    </div>
    <div class="search-row">
      <input id="search-input" type="search" placeholder="Artist, song, vibe…"
             autocomplete="off" autocorrect="off" spellcheck="false"
             oninput="debounceSearch(this.value)">
    </div>
    <div id="results"></div>
  </div>

  <!-- Queue -->
  <div id="queue-section">
    <div class="section-header">
      <span class="section-title">📋 Coming Up</span>
    </div>
    <div id="queue-list"><div style="color:var(--muted);font-size:0.82rem">No suggestions yet</div></div>
  </div>
</div>

<div id="toast"></div>

<script>
const CROSSFADE = {{ crossfade }} * 1000;
let remixMode = false;
let debounceTimer = null;
let lastTrackId = null;
let progressMs = 0;
let durationMs = 1;
let isPlaying = false;
let lastRefresh = 0;

function fmtMs(ms) {
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
}

function toast(msg, color) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = color || '#1DB954';
  t.style.color = color === '#f4a261' ? '#000' : (color ? '#fff' : '#000');
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function triggerCrossfade() {
  const bar = document.getElementById('crossfade-bar');
  bar.classList.remove('fading');
  void bar.offsetWidth; // reflow
  bar.classList.add('fading');
  setTimeout(() => bar.classList.remove('fading'), CROSSFADE + 200);
}

async function refresh() {
  try {
    const r = await fetch('/api/now');
    const d = await r.json();
    if (!d.name) return;

    // Track changed → crossfade animation
    if (d.id && d.id !== lastTrackId) {
      triggerCrossfade();
      // Fade out then update text
      document.getElementById('track-name').style.opacity = '0';
      setTimeout(() => {
        document.getElementById('track-name').textContent = d.name;
        document.getElementById('track-name').style.opacity = '1';
      }, 300);
      lastTrackId = d.id;
    } else {
      document.getElementById('track-name').textContent = d.name;
    }

    document.getElementById('track-artist').textContent = d.artist;
    document.getElementById('track-album').textContent = d.album;

    // Album art + blurred background
    const art = document.getElementById('album-art');
    if (d.album_art && art.src !== d.album_art) {
      art.src = d.album_art;
      document.getElementById('bg-art').style.backgroundImage = `url('${d.album_art}')`;
    }

    // Progress
    progressMs = d.progress_ms;
    durationMs = d.duration_ms || 1;
    isPlaying = d.is_playing;
    lastRefresh = Date.now();
    const pct = Math.round(progressMs / durationMs * 100);
    document.getElementById('progress-fill').style.width = pct + '%';
    document.getElementById('t-now').textContent = fmtMs(progressMs);
    document.getElementById('t-total').textContent = fmtMs(durationMs);

    // Skip votes
    const votes = d.skip_votes, threshold = d.skip_threshold;
    const barPct = Math.round(votes / threshold * 100);
    document.getElementById('vote-bar-fill').style.width = barPct + '%';
    const btn = document.getElementById('skip-btn');
    btn.disabled = d.my_vote;
    btn.classList.toggle('voted', d.my_vote);
    const needed = threshold - votes;
    if (d.my_vote) {
      document.getElementById('vote-text').textContent = `You voted · ${needed} more needed`;
    } else if (votes === 0) {
      document.getElementById('vote-text').textContent = `Be the first to vote`;
    } else {
      document.getElementById('vote-text').textContent = `${votes}/${threshold} votes · ${needed} more to skip`;
    }

    // Queue
    const ql = document.getElementById('queue-list');
    if (d.suggestions && d.suggestions.length) {
      ql.innerHTML = [...d.suggestions].reverse().slice(0, 8).map((s, i) =>
        `<div class="queue-item">
          <span class="queue-num">${i+1}</span>
          <span class="queue-name">${esc(s.name)}</span>
          <span class="queue-artist">${esc(s.artist)}</span>
        </div>`
      ).join('');
    } else {
      ql.innerHTML = '<div style="color:var(--muted);font-size:0.82rem">No suggestions yet</div>';
    }

  } catch(e) {}
}

// Smooth progress ticker between API calls
function tickProgress() {
  if (!isPlaying) return;
  const elapsed = Date.now() - lastRefresh;
  const current = Math.min(progressMs + elapsed, durationMs);
  const pct = Math.round(current / durationMs * 100);
  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('t-now').textContent = fmtMs(current);
}

async function vote() {
  document.getElementById('skip-btn').disabled = true;
  try {
    const r = await fetch('/api/skip', {method:'POST'});
    const d = await r.json();
    if (d.skipped) {
      triggerCrossfade();
      toast('⏭ Skipped!', '#1DB954');
    } else if (d.ok) {
      toast(`${d.votes}/${d.needed} — keep voting!`, '#f4a261');
    } else {
      toast(d.msg || 'Error', '#e63946');
      document.getElementById('skip-btn').disabled = false;
    }
    refresh();
  } catch(e) { document.getElementById('skip-btn').disabled = false; }
}

function toggleRemix() {
  remixMode = !remixMode;
  document.getElementById('remix-pill').classList.toggle('on', remixMode);
  const q = document.getElementById('search-input').value.trim();
  if (q) search(q);
}

function debounceSearch(q) {
  clearTimeout(debounceTimer);
  document.getElementById('results').innerHTML = '';
  if (!q.trim()) return;
  debounceTimer = setTimeout(() => search(q), 450);
}

async function search(q) {
  try {
    const r = await fetch(`/api/search?q=${encodeURIComponent(q)}&remix=${remixMode}`);
    const tracks = await r.json();
    if (!Array.isArray(tracks)) return;
    document.getElementById('results').innerHTML = tracks.map(t => `
      <div class="result-item">
        <img class="result-thumb" src="${t.album_art}" loading="lazy" onerror="this.style.display='none'">
        <div class="result-info">
          <div class="result-name">${esc(t.name)}</div>
          <div class="result-sub">${esc(t.artist)}</div>
        </div>
        <span class="result-dur">${t.duration}</span>
        <button class="add-btn"
          onclick="suggest('${t.uri}','${esc2(t.name)}','${esc2(t.artist)}',this)">
          + Add
        </button>
      </div>`).join('');
  } catch(e) {}
}

async function suggest(uri, name, artist, btn) {
  btn.disabled = true;
  btn.classList.add('added');
  btn.textContent = '✓';
  try {
    const r = await fetch('/api/suggest', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({uri, name, artist})
    });
    const d = await r.json();
    if (d.ok) {
      toast('🎵 Added to queue!');
      document.getElementById('search-input').value = '';
      document.getElementById('results').innerHTML = '';
      refresh();
    } else {
      toast(d.msg || 'Error', '#e63946');
      btn.disabled = false; btn.classList.remove('added'); btn.textContent = '+ Add';
    }
  } catch(e) { btn.disabled = false; btn.classList.remove('added'); btn.textContent = '+ Add'; }
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function esc2(s) {
  return String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/"/g,'\\"');
}

refresh();
setInterval(refresh, 5000);
setInterval(tickProgress, 500);
</script>
</body>
</html>"""


# ── QR + startup ───────────────────────────────────────────────────────────────

def print_qr(url):
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        pass


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--skip-votes", type=int, default=3, dest="skip_votes")
    parser.add_argument("--crossfade", type=int, default=8)
    args = parser.parse_args()

    SKIP_THRESHOLD = args.skip_votes
    CROSSFADE_SECONDS = args.crossfade

    ip = get_local_ip()
    url = f"http://{ip}:{args.port}"

    print(f"\n🎶  Party DJ starting...")
    print(f"📱  Guests open: {url}")
    print(f"⏭   Skip threshold: {SKIP_THRESHOLD} votes  |  Crossfade: {CROSSFADE_SECONDS}s\n")
    print_qr(url)
    print(f"\nCtrl+C to stop.\n")

    threading.Thread(target=track_watcher, daemon=True).start()
    app.run(host="0.0.0.0", port=args.port, debug=False)
