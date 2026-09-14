"""V10 Trust Root - signing and key management.

Key is stored OUTSIDE the code tree at ~/.mimi/keys/constitution.key
with chmod 600. This means editing constitution.py alone is not enough
to forge a valid constitution — the attacker would also need the key.
"""
import hmac
import hashlib
import os
import secrets
from pathlib import Path

KEY_DIR = Path.home() / ".mimi" / "keys"
KEY_PATH = KEY_DIR / "constitution.key"


def _ensure_dir():
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(KEY_DIR, 0o700)
    except Exception:
        pass


def key_exists():
    return KEY_PATH.exists()


def generate_key(overwrite=False):
    _ensure_dir()
    if KEY_PATH.exists() and not overwrite:
        return False, "key already exists"
    raw = secrets.token_bytes(64)
    KEY_PATH.write_bytes(raw)
    try:
        os.chmod(KEY_PATH, 0o600)
    except Exception:
        pass
    return True, "key generated"


def _load_key():
    if not KEY_PATH.exists():
        raise FileNotFoundError(
            f"Constitution key not found at {KEY_PATH}. "
            f"Run: python -m mimi.trust.signer init"
        )
    key = KEY_PATH.read_bytes()
    if len(key) < 32:
        raise ValueError("Key too short — corrupted?")
    return key


def check_key_permissions():
    """Return (ok: bool, msg: str)."""
    if not KEY_PATH.exists():
        return False, "key missing"
    try:
        mode = KEY_PATH.stat().st_mode & 0o777
    except Exception as e:
        return False, f"stat failed: {e}"
    if mode & 0o077:
        return False, f"key is world/group readable (mode={oct(mode)})"
    return True, f"mode={oct(mode)}"


def sign(data: bytes) -> str:
    key = _load_key()
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_signature(data: bytes, expected_hex: str) -> bool:
    try:
        actual = sign(data)
    except Exception:
        return False
    return hmac.compare_digest(actual, expected_hex)


def _sig_path():
    return KEY_DIR / "constitution.sig"


def write_signature(sig_hex: str):
    _ensure_dir()
    _sig_path().write_text(sig_hex.strip())
    try:
        os.chmod(_sig_path(), 0o600)
    except Exception:
        pass


def read_signature():
    p = _sig_path()
    if not p.exists():
        return None
    return p.read_text().strip()


def main():
    """CLI: python -m mimi.trust.signer [init|sign|show]"""
    import sys
    from . import constitution as C

    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"

    if cmd == "init":
        ok, msg = generate_key(overwrite=False)
        print(f"  generate_key: {msg}")
        sig = sign(C.content_bytes())
        write_signature(sig)
        print(f"  signature written: {sig[:16]}...")
        print("  OK. Trust root initialized.")
        return

    if cmd == "resign":
        if not key_exists():
            print("  X no key. run init first.")
            return
        sig = sign(C.content_bytes())
        write_signature(sig)
        print(f"  OK resigned: {sig[:16]}...")
        return

    if cmd == "show":
        print(f"  key path   : {KEY_PATH}")
        print(f"  key exists : {key_exists()}")
        ok, msg = check_key_permissions()
        print(f"  key perms  : {msg}")
        stored = read_signature()
        print(f"  sig stored : {(stored or '(none)')[:16]}...")
        if key_exists():
            actual = sign(C.content_bytes())
            print(f"  sig actual : {actual[:16]}...")
            print(f"  MATCH      : {actual == stored}")
        return

    print("Usage: python -m mimi.trust.signer [init|resign|show]")


if __name__ == "__main__":
    main()
