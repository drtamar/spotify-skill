# Cover Art Upload Troubleshooting

## How the upload works

The skill generates cover art as a **JPEG** file and uploads it to Spotify via:

```
PUT https://api.spotify.com/v1/playlists/{id}/images
Content-Type: image/jpeg
Body: base64-encoded JPEG (≤ 256 KB encoded)
```

Spotify **requires JPEG** — PNG is not accepted. The skill handles the
SVG → JPEG conversion automatically.

---

## Error reference

### 401 Unauthorized — expired token

```
✗ Failed to upload cover art: 401 Unauthorized
Your access token is invalid or expired.
```

Access tokens expire after ~1 hour. **Fix:**

1. Pass your `refresh_token` to `CoverArtGenerator` so it refreshes automatically:

   ```python
   generator = CoverArtGenerator(
       client_id, client_secret, access_token,
       refresh_token=os.getenv("SPOTIFY_REFRESH_TOKEN")
   )
   ```

2. Or re-run `get_refresh_token.py` to get a fresh access token:

   ```bash
   python get_refresh_token.py
   ```

   Then update `SPOTIFY_ACCESS_TOKEN` in your `.env` file.

---

### 403 Forbidden — missing `ugc-image-upload` scope

```
✗ Failed to upload cover art: 403 Forbidden
⚠️  MISSING SCOPE: The 'ugc-image-upload' scope is required.
```

Your token was authorized without the cover-art upload permission. **Fix:**

1. Re-run the OAuth flow:

   ```bash
   python get_refresh_token.py
   ```

   The script already includes `ugc-image-upload` in its scope list.

2. Copy the new **refresh token** to your `.env` file:

   ```
   SPOTIFY_REFRESH_TOKEN=your_new_refresh_token_here
   ```

3. Make sure your redirect URI (`http://127.0.0.1:8888/callback`) is
   registered in your Spotify Developer Dashboard app settings.

---

### 400 Bad Request — wrong image format or over size limit

```
✗ Failed to upload cover art: 400 Bad Request
The image data was rejected. It must be base64-encoded JPEG (not PNG) and ≤ 256 KB once encoded.
```

This should not happen with the current code (JPEG is generated
automatically and the image is optimized to fit). If it does:

- Confirm you're using the latest version of `cover_art_generator.py`.
- Do not pass a `.png` file path directly to `upload_cover_image` — use
  `generate_cover_art()` which produces a properly sized JPEG.

---

### 429 / 5xx — rate limit or Spotify server error

The skill retries automatically (up to 3 times, honouring `Retry-After`).
If it keeps failing, wait a few minutes and try again.

---

## Generating locally, uploading manually

If you want to review the cover art before uploading, or prefer not to
grant upload permission:

```python
jpg_path = generator.generate_cover_art(
    title="My Playlist",
    subtitle="2024",
    theme="summer",
    output_path="my_cover.jpg"
)
print(f"Cover saved to: {jpg_path}")
```

Then in Spotify (web or desktop):
- Go to your playlist → three dots (...) → **Edit details**
- Click **Change image** → select the `.jpg` file → **Save**

---

## Required scopes

| Scope | Required for |
|---|---|
| `playlist-modify-public` / `playlist-modify-private` | All playlist edits |
| `ugc-image-upload` | Uploading cover art via the API |

All other scopes (playback, library, user data) are for other skill features.

---

## Verification

After setting up credentials, run:

```bash
python spotify-api/test_cover_art.py
```

Or quick inline test (no playlist needed):

```bash
python -c "
import os, sys
sys.path.insert(0, 'spotify-api/scripts')
from cover_art_generator import CoverArtGenerator
gen = CoverArtGenerator(
    os.getenv('SPOTIFY_CLIENT_ID'),
    os.getenv('SPOTIFY_CLIENT_SECRET'),
    os.getenv('SPOTIFY_ACCESS_TOKEN'),
    refresh_token=os.getenv('SPOTIFY_REFRESH_TOKEN'),
)
path = gen.generate_cover_art(title='Test', theme='energetic', output_path='test.jpg')
print(f'✓ JPEG generated: {path}')
"
```

---

## Feature availability

| Feature | Requires `ugc-image-upload`? |
|---|---|
| Generate JPEG locally | No |
| Save to disk | No |
| Upload to Spotify via API | **Yes** |
