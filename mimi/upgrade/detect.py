"""V10 Upgrade Lab - self-diagnosis.

Detector scans the system and creates proposals for problems it finds.
Detection is read-only; it only writes to upgrade_proposals (never to
production code).
"""
import importlib
import sys
from pathlib import Path

from ..database import BASE_DIR, fetch_one, table_exists, get_tables
from ..guardian import audit
from . import proposal


def _pkg_dir():
    return Path(BASE_DIR) / "mimi"


def _list_modules():
    p = _pkg_dir()
    return sorted(f.stem for f in p.glob("*.py") if f.stem != "__init__")


def _check_module_imports():
    """Try importing every module; return broken list."""
    broken = []
    for m in _list_modules():
        name = f"mimi.{m}"
        if name in sys.modules:
            continue
        try:
            importlib.import_module(name)
        except Exception as e:
            broken.append({
                "module": m,
                "error": f"{type(e).__name__}: {e}",
            })
    return broken


def _check_required_tables():
    required = [
        "goals", "missions", "tasks", "study_sessions", "finance",
        "debts", "daily_logs", "journal", "time_logs", "sleep",
        "routines", "productivity",
        "system_logs", "recommendations", "intelligence_logs",
    ]
    missing = [t for t in required if not table_exists(t)]
    return missing


def _check_orphan_records():
    """Rows whose foreign key points to nothing (soft check)."""
    issues = []
    try:
        r = fetch_one(
            """SELECT COUNT(*) FROM tasks t
               WHERE t.mission_id IS NOT NULL
               AND NOT EXISTS (SELECT 1 FROM missions m WHERE m.id=t.mission_id)""")
        n = r[0] if r else 0
        if n:
            issues.append({
                "category": "data_integrity",
                "module": "tasks",
                "problem": f"{n} task(s) reference missing missions",
                "proposal": "clear orphan mission_id, or re-link to valid mission",
                "risk": "low",
            })
    except Exception:
        pass
    return issues


def _check_duplicate_motto():
    """Motto should be unique in system_config."""
    try:
        r = fetch_one(
            """SELECT COUNT(*) FROM system_config WHERE key='motto'""")
        n = r[0] if r else 0
        if n > 1:
            return [{
                "category": "data_integrity",
                "module": "system_config",
                "problem": f"duplicate 'motto' key ({n} rows)",
                "proposal": "keep newest, delete duplicates",
                "risk": "low",
            }]
    except Exception:
        pass
    return []


def _check_audit_chain():
    try:
        from ..guardian.audit import verify_chain
        ok, msg, n = verify_chain()
        if not ok:
            return [{
                "category": "security",
                "module": "guardian.audit",
                "problem": f"audit chain broken: {msg}",
                "proposal": "investigate tamper; do NOT auto-fix (inform owner)",
                "risk": "critical",
            }]
    except Exception:
        pass
    return []


def _check_trust_root():
    try:
        from ..trust.verify import verify_constitution
        ok, reason = verify_constitution()
        if not ok:
            return [{
                "category": "security",
                "module": "trust",
                "problem": f"constitution not verified: {reason}",
                "proposal": "run: python -m mimi.trust.signer resign",
                "risk": "critical",
            }]
    except Exception:
        pass
    return []


def _check_disk_space():
    try:
        import shutil
        u = shutil.disk_usage(str(BASE_DIR))
        free_mb = u.free // (1024 * 1024)
        if free_mb < 50:
            return [{
                "category": "system",
                "module": "disk",
                "problem": f"low disk space: {free_mb} MB free",
                "proposal": "clean old backups / exports / reports",
                "risk": "medium",
            }]
    except Exception:
        pass
    return []


def scan():
    """Run all checks. Return list of finding dicts."""
    findings = []

    # 1. Broken imports
    for b in _check_module_imports():
        findings.append({
            "category": "code",
            "module": b["module"],
            "problem": f"import error: {b['error']}",
            "proposal": "investigate import error; propose fix",
            "risk": "high",
        })

    # 2. Missing tables
    missing = _check_required_tables()
    for t in missing:
        findings.append({
            "category": "schema",
            "module": t,
            "problem": f"required table '{t}' missing",
            "proposal": "run schema bootstrap (ensure_schema)",
            "risk": "high",
        })

    # 3. Data integrity
    findings += _check_orphan_records()
    findings += _check_duplicate_motto()

    # 4. Security
    findings += _check_audit_chain()
    findings += _check_trust_root()

    # 5. System
    findings += _check_disk_space()

    audit.log("detect_scan", actor="lab",
              payload={"findings": len(findings)})
    return findings


def to_proposals(findings=None):
    """Convert findings into proposals (dedup against pending)."""
    if findings is None:
        findings = scan()

    existing = {
        (p["category"], p["module"], p["problem"])
        for p in proposal.pending()
    }
    created = []
    for f in findings:
        key = (f["category"], f["module"], f["problem"])
        if key in existing:
            continue
        pid = proposal.create(
            category=f["category"],
            module=f["module"],
            problem=f["problem"],
            proposal=f["proposal"],
            risk_level=f["risk"],
        )
        if pid:
            created.append(pid)
    return created


def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        findings = scan()
        print(f"  findings: {len(findings)}")
        for f in findings:
            print(f"    [{f['risk']:<8}] {f['category']:<16} "
                  f"{f['module']:<20} {f['problem'][:60]}")
    elif cmd == "propose":
        ids = to_proposals()
        print(f"  created {len(ids)} proposal(s): {ids}")
    else:
        print("usage: python -m mimi.upgrade.detect [scan|propose]")


if __name__ == "__main__":
    main()
