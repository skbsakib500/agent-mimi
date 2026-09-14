"""V10 Trust Root - verification at runtime.

Any module that wants to act as 'Mimi' MUST call verify_constitution()
first and refuse to act if it returns False.
"""
from . import constitution as C
from . import signer


def verify_constitution(raise_on_fail=False):
    """Return (ok: bool, reason: str)."""
    # 1. Key exists + permissions strict
    if not signer.key_exists():
        return _fail("constitution key missing", raise_on_fail)
    ok, msg = signer.check_key_permissions()
    if not ok:
        return _fail(f"key permissions weak: {msg}", raise_on_fail)

    # 2. Signature file exists
    stored = signer.read_signature()
    if not stored:
        return _fail("no signature on file", raise_on_fail)

    # 3. Content matches signature
    actual = signer.sign(C.content_bytes())
    if actual != stored:
        return _fail(
            "signature mismatch — constitution text has been modified "
            "without re-signing", raise_on_fail)

    return True, "verified"


def _fail(reason, raise_on_fail):
    try:
        from ..database import execute
        execute(
            """INSERT INTO system_logs (log_type, message)
               VALUES (?, ?)""",
            ("trust_violation", reason),
        )
    except Exception:
        pass
    if raise_on_fail:
        raise RuntimeError(f"Constitution verification failed: {reason}")
    return False, reason


def main():
    ok, reason = verify_constitution()
    if ok:
        print(f"  OK constitution VERIFIED ({reason})")
    else:
        print(f"  X TAMPERED or MISSING: {reason}")
        print("  Refusing to trust this installation.")
        print("  Fix: python -m mimi.trust.signer resign")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
