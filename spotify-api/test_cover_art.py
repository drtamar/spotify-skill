"""
Tests for cover_art_generator.py — upload pipeline and image optimization.

Run from the repo root:
    python -m pytest spotify-api/test_cover_art.py -v
Or directly:
    python spotify-api/test_cover_art.py
"""

import base64
import os
import sys
import tempfile
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from cover_art_generator import CoverArtGenerator  # noqa: E402


def _make_generator(access_token="tok", refresh_token=None):
    return CoverArtGenerator(
        client_id="cid",
        client_secret="csec",
        access_token=access_token,
        refresh_token=refresh_token,
    )


def _jpeg_bytes(size_bytes: int = 100) -> bytes:
    """Return a valid 1×1 JPEG padded to roughly `size_bytes`."""
    try:
        from PIL import Image
        buf = BytesIO()
        Image.new("RGB", (1, 1), color=(255, 0, 0)).save(buf, format="JPEG")
        data = buf.getvalue()
        # pad with JPEG comment markers so the size grows but it stays valid
        while len(data) < size_bytes:
            extra = size_bytes - len(data)
            chunk = b"\xff\xfe" + extra.to_bytes(2, "big") + b"\x00" * (extra - 2)
            data = data[:-2] + chunk + data[-2:]
            break
        return data
    except ImportError:
        return b"\xff\xd8\xff\xe0" + b"\x00" * max(0, size_bytes - 4) + b"\xff\xd9"


class TestUploadCoverImage(unittest.TestCase):

    def _upload(self, status, generator=None, text="", headers=None):
        gen = generator or _make_generator()
        response = MagicMock()
        response.status_code = status
        response.text = text
        response.headers = headers or {}
        jpeg = _jpeg_bytes(100)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(jpeg)
            path = f.name
        try:
            with patch("requests.put", return_value=response) as mock_put:
                result = gen.upload_cover_image("playlist123", path)
            return result, mock_put
        finally:
            os.unlink(path)

    def test_202_returns_true(self):
        result, mock_put = self._upload(202)
        self.assertTrue(result)

    def test_payload_is_valid_base64_jpeg(self):
        """The PUT body must be base64-encoded JPEG bytes."""
        _, mock_put = self._upload(202)
        call_kwargs = mock_put.call_args
        body = call_kwargs[1].get("data") or call_kwargs[0][2]
        raw = base64.b64decode(body)
        self.assertTrue(raw[:2] == b"\xff\xd8", "Payload is not JPEG")

    def test_content_type_header_is_image_jpeg(self):
        _, mock_put = self._upload(202)
        headers = mock_put.call_args[1]["headers"]
        self.assertEqual(headers["Content-Type"], "image/jpeg")

    def test_401_expired_token_tries_refresh(self):
        """A 401 should attempt a token refresh before giving up."""
        gen = _make_generator(refresh_token="rtoken")
        refresh_resp = MagicMock()
        refresh_resp.status_code = 200
        refresh_resp.json.return_value = {"access_token": "new_tok"}

        fail_resp = MagicMock(status_code=401, text="Unauthorized", headers={})
        ok_resp = MagicMock(status_code=202, text="", headers={})

        jpeg = _jpeg_bytes(100)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(jpeg)
            path = f.name
        try:
            with patch("requests.put", side_effect=[fail_resp, ok_resp]), \
                 patch("requests.post", return_value=refresh_resp):
                result = gen.upload_cover_image("pid", path)
        finally:
            os.unlink(path)
        self.assertTrue(result)
        self.assertEqual(gen.access_token, "new_tok")

    def test_401_no_refresh_token_returns_false(self):
        result, _ = self._upload(401)
        self.assertFalse(result)

    def test_403_returns_false(self):
        result, _ = self._upload(403)
        self.assertFalse(result)

    def test_400_returns_false(self):
        result, _ = self._upload(400)
        self.assertFalse(result)

    def test_429_retries_with_backoff(self):
        ok_resp = MagicMock(status_code=202, text="", headers={})
        rate_resp = MagicMock(status_code=429, text="", headers={"Retry-After": "0"})
        jpeg = _jpeg_bytes(100)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(jpeg)
            path = f.name
        gen = _make_generator()
        try:
            with patch("requests.put", side_effect=[rate_resp, ok_resp]), \
                 patch("time.sleep"):
                result = gen.upload_cover_image("pid", path)
        finally:
            os.unlink(path)
        self.assertTrue(result)

    def test_oversized_payload_rejected_before_request(self):
        """Images whose base64 size exceeds 256 KB must be rejected locally."""
        gen = _make_generator()
        # Write a fake "JPEG" that is definitely over 256 KB raw
        big = b"\xff\xd8" + b"\x00" * (300 * 1024) + b"\xff\xd9"
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(big)
            path = f.name
        try:
            with patch("requests.put") as mock_put:
                result = gen.upload_cover_image("pid", path)
            mock_put.assert_not_called()
        finally:
            os.unlink(path)
        self.assertFalse(result)


class TestOptimizeImage(unittest.TestCase):

    def _make_jpeg(self, width=800, height=800) -> str:
        """Write a large JPEG to a temp file and return its path."""
        from PIL import Image
        img = Image.new("RGB", (width, height), color=(128, 0, 64))
        fd, path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        img.save(path, format="JPEG", quality=95)
        return path

    def test_output_stays_within_encoded_limit(self):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self.skipTest("Pillow not installed")
        gen = _make_generator()
        path = self._make_jpeg(800, 800)
        try:
            gen._optimize_image(path, max_size_kb=256)
            with open(path, "rb") as f:
                data = f.read()
            encoded_size = CoverArtGenerator._encoded_size(data)
            self.assertLessEqual(
                encoded_size, 256 * 1024,
                f"Encoded size {encoded_size} exceeds 256 KB"
            )
        finally:
            os.unlink(path)

    def test_output_is_jpeg(self):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self.skipTest("Pillow not installed")
        gen = _make_generator()
        path = self._make_jpeg(600, 600)
        try:
            gen._optimize_image(path, max_size_kb=256)
            with open(path, "rb") as f:
                header = f.read(2)
            self.assertEqual(header, b"\xff\xd8", "Output is not a JPEG")
        finally:
            os.unlink(path)

    def test_encoded_size_helper(self):
        data = b"A" * 100
        self.assertEqual(CoverArtGenerator._encoded_size(data),
                         len(base64.b64encode(data)))


if __name__ == "__main__":
    unittest.main()
