"""V10 Guardian - append-only audit log.

Stored as JSONL at data/audit.jsonl. Each line = one signed event.
Signed with the same key as the constitution, so tampering with
past lines is detectable.
"""
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

from ..database import DATA_DIR
from ..trust.signer import sign

AUDIT_PATH = DATA_DIR / "audit.jsonl"
CHAIN_PATH = DATA_DIR / "audit.chain"


def _ensure():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _prev_hash():
    if not CHAIN_PATH.exists():
        return "GENESIS"
    try:
        return CHAIN_PATH.read_text().strip() or "GENESIS"
    except Exception:
        return "GENESIS"


def _update_chain(h):
    _ensure()
    CHAIN_PATH.write_text(h)
    try:
        os.chmod(CHAIN_PATH, 0o600)
    except Exception:
        pass


def log(event_type, actor="system", payload=None):
    """Append a signed event. Returns the event hash."""
    _ensure()
    prev = _prev_hash()
    ts = datetime.now().isoformat(timespec="microseconds")
    body = {
        "ts": ts,
        "actor": str(actor),
        "event": str(event_type),
        "prev": prev,
        "payload": payload or {},
    }
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False)
    try:
        sig = sign(canonical.encode("utf-8"))
    except Exception:
        sig = "UNSIGNED"
    body["sig"] = sig
    line = json.dumps(body, ensure_ascii=False, sort_keys=True)

    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

    h = hashlib.sha256(line.encode("utf-8")).hexdigest()
    _update_chain(h)
    return h


def verify_chain():
    """Walk the log and detect tampering. Returns (ok, msg, count)."""
    if not AUDIT_PATH.exists():
        return True, "no log yet", 0
    count = 0
    prev = "GENESIS"
    with AUDIT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                return False, f"line {count+1}: not JSON", count
            if ev.get("prev") != prev:
                return False, f"line {count+1}: broken chain link", count
            body = {k: ev[k] for k in ("ts", "actor", "event", "prev", "payload")}
            canonical = json.dumps(body, sort_keys=True, ensure_ascii=False)
            try:
                expect = sign(canonical.encode("utf-8"))
            except Exception:
                expect = "UNSIGNED"
            if ev.get("sig") != expect:
                return False, f"line {count+1}: signature mismatch", count
            prev = hashlib.sha256(line.encode("utf-8")).hexdigest()
            count += 1
    return True, "verified", count


def tail(n=20):
    if not AUDIT_PATH.exists():
        return []
    lines = AUDIT_PATH.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "verify":
        ok, msg, n = verify_chain()
        mark = "OK" if ok else "X"
        print(f"  {mark} audit chain: {msg} ({n} events)")
        return 0 if ok else 1
    if cmd == "tail":
        for e in tail(20):
            print(f"  {e['ts']}  [{e['actor']}]  {e['event']}")
        return 0
    if cmd == "test":
        log("test_event", actor="cli", payload={"note": "hello"})
        print("  OK wrote test event")
        return 0
    print("Usage: python -m mimi.guardian.audit [verify|tail|test]")
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
