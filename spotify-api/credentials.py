"""
Credential encryption for Spotify Skill — zero external dependencies.

Scheme: PBKDF2-HMAC-SHA256 key derivation + HMAC-SHA256 stream cipher (CTR mode)
        with HMAC authentication tag. Tamper-proof and password-protected.

Usage (CLI):
    python credentials.py encrypt        # .env → .env.encrypted (safe to commit)
    python credentials.py decrypt        # .env.encrypted → .env.decrypted (inspect only)
    python credentials.py load           # test: decrypt and show key names

Usage (import):
    from credentials import load_credentials
    load_credentials()   # prompts once, injects into os.environ
"""

import base64
import getpass
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"
ENCRYPTED_FILE = Path(__file__).parent / ".env.encrypted"

PBKDF2_ITERATIONS = 480_000


# ── Crypto primitives (stdlib only) ───────────────────────────────────────────

def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    """HMAC-SHA256 counter-mode keystream."""
    stream = bytearray()
    counter = 0
    while len(stream) < length:
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"), "sha256").digest()
        stream.extend(block)
        counter += 1
    return bytes(stream[:length])


def _xor(data: bytes, keystream: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, keystream))


def _encrypt_bytes(plaintext: bytes, password: str) -> dict:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(password, salt)
    ciphertext = _xor(plaintext, _keystream(key, nonce, len(plaintext)))
    mac = hmac.new(key, nonce + ciphertext, "sha256").digest()
    return {
        "salt": salt.hex(),
        "nonce": nonce.hex(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "mac": mac.hex(),
    }


def _decrypt_bytes(payload: dict, password: str) -> bytes:
    salt = bytes.fromhex(payload["salt"])
    nonce = bytes.fromhex(payload["nonce"])
    ciphertext = base64.b64decode(payload["ciphertext"])
    stored_mac = bytes.fromhex(payload["mac"])

    key = _derive_key(password, salt)

    expected_mac = hmac.new(key, nonce + ciphertext, "sha256").digest()
    if not hmac.compare_digest(stored_mac, expected_mac):
        raise ValueError("Wrong password or file is corrupted.")

    return _xor(ciphertext, _keystream(key, nonce, len(ciphertext)))


# ── Public API ─────────────────────────────────────────────────────────────────

def encrypt(password: str | None = None) -> None:
    if not ENV_FILE.exists():
        print(f"ERROR: {ENV_FILE} not found.")
        sys.exit(1)

    if password is None:
        password = getpass.getpass("Set encryption password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.")
            sys.exit(1)

    payload = _encrypt_bytes(ENV_FILE.read_bytes(), password)
    ENCRYPTED_FILE.write_text(json.dumps(payload, indent=2))

    print(f"✅  Encrypted → {ENCRYPTED_FILE}")
    print(f"    Safe to commit to git.")
    print(f"⚠️   Delete {ENV_FILE} once you have confirmed the encrypted file works.")


def decrypt_to_file(password: str | None = None) -> None:
    password = password or getpass.getpass("Password: ")
    payload = json.loads(ENCRYPTED_FILE.read_text())
    text = _decrypt_bytes(payload, password).decode()
    out = ENV_FILE.with_suffix(".decrypted")
    out.write_text(text)
    print(f"✅  Decrypted → {out}  (delete after inspection)")


def load_credentials(password: str | None = None) -> None:
    """Decrypt .env.encrypted and inject values into os.environ."""

    # Prefer plaintext .env if present (dev convenience)
    if ENV_FILE.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(ENV_FILE)
        except ImportError:
            _inject_env(ENV_FILE.read_text())
        return

    if not ENCRYPTED_FILE.exists():
        raise FileNotFoundError(
            f"No credentials found.\n"
            f"Add your keys to {ENV_FILE} then run:\n"
            f"  python credentials.py encrypt"
        )

    if password is None:
        password = os.environ.get("DJ_PASSWORD")
    if password is None:
        password = getpass.getpass("Spotify credentials password: ")

    payload = json.loads(ENCRYPTED_FILE.read_text())
    text = _decrypt_bytes(payload, password).decode()
    _inject_env(text)


def _inject_env(text: str) -> None:
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "encrypt":
        encrypt()
    elif cmd == "decrypt":
        decrypt_to_file()
    elif cmd == "load":
        load_credentials()
        keys = [k for k in os.environ if k.startswith("SPOTIFY_")]
        print("✅  Loaded:", ", ".join(keys))
    else:
        print(__doc__)
