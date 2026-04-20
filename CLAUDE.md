# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all dependencies (includes cover art image generation libraries)
pip install -r spotify-api/requirements.txt

# Validate skill structure
python tools/validate_skill.py ./spotify-api

# Test Spotify credentials
python spotify-api/scripts/test_credentials.py

# Generate OAuth refresh token (interactive browser flow)
python get_refresh_token.py

# Export user data to JSON
python spotify-api/scripts/export_data.py

# Create a new skill from template
python tools/init_skill.py <skill-name> --path ./

# Package a skill for distribution
python tools/package_skill.py ./spotify-api ./dist
```

## Architecture

This project serves two purposes: a **production Spotify API skill** and a **skill development platform**.

### Skill System (Agent Skills Spec v1.0)

Skills are folders with a `SKILL.md` entry point containing YAML frontmatter (`name`, `description`) followed by Markdown content. The name must match the directory name in hyphen-case. Optional subdirectories: `scripts/` (Python/shell), `references/` (docs), `assets/` (static files). See `agent_skills_spec.md` for the full spec.

### Spotify Skill (`spotify-api/`)

The skill has three Python modules in `scripts/` that depend on each other:

- **`spotify_client.py`** — Base layer. `SpotifyClient` handles all OAuth 2.0 token management (auto-refresh) and raw API calls via `_make_request()`. `SpotifyAPIWrapper` wraps it with higher-level error handling. Credentials load from `spotify-api/.env` using `create_client_from_env()`. The top-item method is `get_top_items(item_type="artists"|"tracks", ...)` — there are no separate `get_user_top_artists()` or `get_user_top_tracks()` methods.

- **`playlist_creator.py`** — Middle layer. `PlaylistCreator` takes a `SpotifyClient` and provides 5 strategies: by artist, theme/keywords, lyrics, song list, or recommendations. Handles deduplication and batch processing internally.

- **`cover_art_generator.py`** — Standalone image pipeline. Generates SVG → converts to PNG via `cairosvg` → optimizes with `Pillow` → uploads directly to Spotify. Requires both `cairosvg` and `pillow` to import. Always read `references/COVER_ART_LLM_GUIDE.md` before generating cover art — it defines the content-driven color analysis workflow (preferred over the legacy preset `THEME_COLORS` dict).

### Development Tools (`tools/`)

- `init_skill.py` — scaffolds a new skill directory with a template SKILL.md
- `validate_skill.py` — checks SKILL.md frontmatter, naming conventions, TODO completeness
- `package_skill.py` — creates a distributable `.zip`, excluding system files

### Credentials Flow

Scripts look for `spotify-api/.env` (copy `.env.example`). The `SPOTIFY_REFRESH_TOKEN` is the critical credential — run `get_refresh_token.py` once to obtain it via browser OAuth. Access tokens auto-refresh from it at runtime.
