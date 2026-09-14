"""V10 Trust Root - loader.

Call ensure_trusted() at the top of any boot path. It verifies the
constitution and refuses to proceed if trust is broken.
"""
from .verify import verify_constitution

_verified_once = {"ok": None, "reason": ""}


def ensure_trusted(fail_closed=True):
    """Return True if trusted. Caches result per-process.

    fail_closed=True (default): raise RuntimeError if not trusted.
    fail_closed=False: return False without raising.
    """
    if _verified_once["ok"] is True:
        return True
    ok, reason = verify_constitution(raise_on_fail=False)
    _verified_once["ok"] = ok
    _verified_once["reason"] = reason
    if not ok and fail_closed:
        raise RuntimeError(
            "Mimi refuses to boot: trust check failed — " + reason
        )
    return ok


def reason():
    return _verified_once["reason"]


def reset_cache():
    _verified_once["ok"] = None
    _verified_once["reason"] = ""
