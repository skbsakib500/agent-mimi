"""V10 Upgrade Lab - proposal state machine.

States:
  DETECTED -> PROPOSED -> SANDBOX_TESTING -> WAITING_APPROVAL
                                                |
                                    +-----------+-----------+
                                    v                       v
                                APPROVED                REJECTED
                                    |
                                    v
                                APPLYING
                                    |
                          +---------+---------+
                          v                   v
                      VERIFIED            FAILED
                                              |
                                              v
                                        ROLLED_BACK
"""
import json
from datetime import datetime
from ..database import execute, fetch_one, fetch_all
from ..guardian import audit
from ..guardian.permissions import check


VALID_STATES = {
    "DETECTED", "PROPOSED", "SANDBOX_TESTING", "WAITING_APPROVAL",
    "APPROVED", "REJECTED", "APPLYING", "VERIFIED",
    "FAILED", "ROLLED_BACK",
}

# Legal transitions
TRANSITIONS = {
    "DETECTED":         {"PROPOSED", "REJECTED"},
    "PROPOSED":         {"SANDBOX_TESTING", "WAITING_APPROVAL", "REJECTED"},
    "SANDBOX_TESTING":  {"WAITING_APPROVAL", "FAILED"},
    "WAITING_APPROVAL": {"APPROVED", "REJECTED"},
    "APPROVED":         {"APPLYING", "REJECTED"},
    "REJECTED":         set(),
    "APPLYING":         {"VERIFIED", "FAILED"},
    "VERIFIED":         set(),
    "FAILED":           {"ROLLED_BACK"},
    "ROLLED_BACK":      set(),
}


def ensure_table():
    execute("""CREATE TABLE IF NOT EXISTS upgrade_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        category TEXT NOT NULL,
        module TEXT,
        problem TEXT,
        proposal TEXT,
        risk_level TEXT DEFAULT 'low',
        files_changed TEXT,
        backup_id TEXT,
        sandbox_result TEXT,
        verify_result TEXT,
        status TEXT DEFAULT 'DETECTED',
        approved_by TEXT,
        approved_at TEXT)""")


def _row(r):
    if not r:
        return None
    d = dict(r)
    for k in ("files_changed", "sandbox_result", "verify_result"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                pass
    return d


def create(category, module="", problem="", proposal="",
           risk_level="low", files=None):
    ensure_table()
    p = {
        "category": category,
        "module": module,
        "problem": problem,
        "proposal": proposal,
        "risk_level": risk_level,
        "files_changed": json.dumps(files or []),
    }
    cur = execute(
        """INSERT INTO upgrade_proposals
           (category, module, problem, proposal, risk_level, files_changed, status)
           VALUES (?, ?, ?, ?, ?, ?, 'PROPOSED')""",
        (category, module, problem, proposal, risk_level,
         p["files_changed"]))
    pid = cur.lastrowid if hasattr(cur, "lastrowid") else None
    audit.log("upgrade_proposed", actor="lab",
              payload={"category": category, "module": module,
                       "risk": risk_level})
    return pid


def get(pid):
    ensure_table()
    return _row(fetch_one(
        "SELECT * FROM upgrade_proposals WHERE id=?", (int(pid),)))


def list_all(limit=50):
    ensure_table()
    rows = fetch_all(
        """SELECT * FROM upgrade_proposals
           ORDER BY id DESC LIMIT ?""", (int(limit),))
    return [_row(r) for r in rows]


def list_by_status(status):
    ensure_table()
    rows = fetch_all(
        """SELECT * FROM upgrade_proposals WHERE status=?
           ORDER BY id DESC""", (status,))
    return [_row(r) for r in rows]


def pending():
    ensure_table()
    rows = fetch_all(
        """SELECT * FROM upgrade_proposals
           WHERE status IN ('PROPOSED','SANDBOX_TESTING','WAITING_APPROVAL',
                            'APPROVED','APPLYING')
           ORDER BY id DESC""")
    return [_row(r) for r in rows]


def can_transition(frm, to):
    return to in TRANSITIONS.get(frm, set())


def transition(pid, new_status, *, note=None, actor="lab",
               approved_by=None, extra=None):
    """Move to new status. Enforces state machine + permission gate."""
    p = get(pid)
    if not p:
        return False, "proposal not found"
    frm = p["status"]
    if not can_transition(frm, new_status):
        return False, f"illegal transition {frm} -> {new_status}"

    # Sensitive transitions require owner
    sensitive = {"APPROVED", "APPLYING", "ROLLED_BACK"}
    if new_status in sensitive:
        ok, reason = check("upgrade_apply", actor=actor,
                            approved_by=approved_by)
        if not ok:
            return False, reason

    fields = ["status=?", "updated_at=CURRENT_TIMESTAMP"]
    params = [new_status]
    if note:
        fields.append("verify_result=?")
        params.append(json.dumps({"note": note}))
    if extra:
        for k, v in extra.items():
            if k in ("backup_id", "sandbox_result", "verify_result",
                     "files_changed"):
                fields.append(f"{k}=?")
                params.append(json.dumps(v) if isinstance(v, (list, dict)) else v)
    if new_status == "APPROVED":
        fields.append("approved_by=?")
        params.append(approved_by or "SKB Sakib")
        fields.append("approved_at=CURRENT_TIMESTAMP")
    params.append(int(pid))

    execute(f"UPDATE upgrade_proposals SET {', '.join(fields)} WHERE id=?",
            tuple(params))
    audit.log("upgrade_transition", actor=actor,
              payload={"id": int(pid), "from": frm, "to": new_status,
                       "note": note or ""})
    return True, f"{frm} -> {new_status}"


def main():
    """CLI helper: python -m mimi.upgrade.proposal"""
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        for p in list_all():
            print(f"  #{p['id']:<4} [{p['status']:<16}] "
                  f"{p['category']:<12} {p['module']:<10} "
                  f"{(p['problem'] or '')[:40]}")
    elif cmd == "pending":
        for p in pending():
            print(f"  #{p['id']:<4} [{p['status']:<16}] {p['problem'][:50]}")
    elif cmd == "create":
        pid = create("test", "demo",
                     "test problem", "test proposal", "low")
        print(f"  OK created proposal #{pid}")
    elif cmd == "get":
        if len(sys.argv) < 3:
            print("usage: get <id>"); return
        p = get(sys.argv[2])
        if not p:
            print("  not found"); return
        for k, v in p.items():
            print(f"  {k}: {v}")
    else:
        print("usage: list|pending|create|get <id>")


if __name__ == "__main__":
    main()
