"""V10 Health Diagnostic.

Every check is read-only. Returns a structured report:
  {ok_count, warn_count, fail_count, sections[], elapsed_sec}
"""
import importlib
import shutil
import sys
import time
from pathlib import Path

from ..database import BASE_DIR, DB_PATH, get_tables, table_exists

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"


class Check:
    __slots__ = ("section", "name", "status", "detail")

    def __init__(self, section, name, status, detail=""):
        self.section = section
        self.name = name
        self.status = status
        self.detail = detail

    def dict(self):
        return {"section": self.section, "name": self.name,
                "status": self.status, "detail": self.detail}


# ─────────────── section: CORE ───────────────

def _check_python():
    v = sys.version_info
    s = f"{v.major}.{v.minor}.{v.micro}"
    if v.major == 3 and v.minor >= 10:
        return Check("Core", "Python version", OK, s)
    return Check("Core", "Python version", FAIL, f"{s} (need 3.10+)")


def _check_curses():
    try:
        import curses  # noqa: F401
        return Check("Core", "curses (TUI)", OK, "available")
    except Exception as e:
        return Check("Core", "curses (TUI)", WARN,
                     f"{type(e).__name__}: {e}")


def _check_core_modules():
    mods = ["mimi.core.bus", "mimi.core.registry", "mimi.core.orchestrator"]
    broken = []
    for m in mods:
        try:
            importlib.import_module(m)
        except Exception as e:
            broken.append(f"{m}: {type(e).__name__}")
    if broken:
        return Check("Core", "Core modules", FAIL, ", ".join(broken))
    return Check("Core", "Core modules", OK, f"{len(mods)} loaded")


# ─────────────── section: DATABASE ───────────────

def _check_db_exists():
    if DB_PATH.exists():
        size_kb = DB_PATH.stat().st_size // 1024
        return Check("Database", "DB file", OK, f"{size_kb} KB")
    return Check("Database", "DB file", FAIL, "missing")


def _check_tables():
    try:
        tabs = get_tables()
        n = len(tabs)
        if n < 5:
            return Check("Database", "Tables", WARN, f"only {n}")
        return Check("Database", "Tables", OK, f"{n} tables")
    except Exception as e:
        return Check("Database", "Tables", FAIL,
                     f"{type(e).__name__}: {e}")


def _check_required_tables():
    required = ["goals", "missions", "tasks", "study_sessions",
                "finance", "debts", "journal", "system_logs"]
    missing = [t for t in required if not table_exists(t)]
    if missing:
        return Check("Database", "Required tables", FAIL,
                     f"missing: {', '.join(missing[:3])}")
    return Check("Database", "Required tables", OK, f"{len(required)} present")


def _check_integrity():
    try:
        import sqlite3
        c = sqlite3.connect(str(DB_PATH))
        try:
            r = c.execute("PRAGMA integrity_check").fetchone()
            ok = r[0] if r else "?"
        finally:
            c.close()
        if ok == "ok":
            return Check("Database", "Integrity", OK, "ok")
        return Check("Database", "Integrity", FAIL, str(ok)[:60])
    except Exception as e:
        return Check("Database", "Integrity", FAIL,
                     f"{type(e).__name__}: {e}")


# ─────────────── section: TRUST ───────────────

def _check_trust_root():
    try:
        from ..trust.verify import verify_constitution
        ok, reason = verify_constitution()
        if ok:
            return Check("Trust", "Constitution", OK, "verified")
        return Check("Trust", "Constitution", FAIL, reason[:60])
    except Exception as e:
        return Check("Trust", "Constitution", FAIL,
                     f"{type(e).__name__}: {e}")


def _check_key_perms():
    try:
        from ..trust.signer import check_key_permissions, key_exists
        if not key_exists():
            return Check("Trust", "Key file", FAIL, "missing")
        ok, msg = check_key_permissions()
        return Check("Trust", "Key file", OK if ok else FAIL, msg)
    except Exception as e:
        return Check("Trust", "Key file", FAIL,
                     f"{type(e).__name__}: {e}")


def _check_audit_chain():
    try:
        from ..guardian.audit import verify_chain
        ok, msg, n = verify_chain()
        if ok:
            return Check("Trust", "Audit chain", OK, f"{n} events")
        return Check("Trust", "Audit chain", FAIL, msg[:60])
    except Exception as e:
        return Check("Trust", "Audit chain", FAIL,
                     f"{type(e).__name__}: {e}")


# ─────────────── section: GUARDIAN ───────────────

def _check_permissions():
    try:
        from ..guardian.permissions import POLICY, check
        n = len(POLICY)
        ok, _ = check("read", actor="diag")
        if not ok:
            return Check("Guardian", "Permission gate", FAIL,
                         "read blocked")
        return Check("Guardian", "Permission gate", OK, f"{n} policies")
    except Exception as e:
        return Check("Guardian", "Permission gate", FAIL,
                     f"{type(e).__name__}: {e}")


def _check_no_refuse_bypass():
    """Confirm refused ops really refuse, even with owner approval."""
    try:
        from ..guardian.permissions import check
        ok, reason = check("drop_database",
                            actor="diag",
                            approved_by="SKB Sakib")
        if ok:
            return Check("Guardian", "Refuse-list", FAIL,
                         "refused op was allowed (BUG)")
        return Check("Guardian", "Refuse-list", OK, "refuses correctly")
    except Exception as e:
        return Check("Guardian", "Refuse-list", FAIL,
                     f"{type(e).__name__}: {e}")


# ─────────────── section: AGENTS ───────────────

AGENT_MODULES = [
    ("pa", "mimi.agents.pa"),
    ("manager", "mimi.agents.manager"),
    ("accountant", "mimi.agents.accountant"),
    ("civil", "mimi.agents.civil"),
    ("legal", "mimi.agents.legal"),
    ("advisor", "mimi.agents.advisor"),
]


def _check_agents():
    loaded = []
    broken = []
    for name, mod in AGENT_MODULES:
        try:
            importlib.import_module(mod)
            loaded.append(name)
        except Exception as e:
            broken.append(f"{name}: {type(e).__name__}")
    if broken:
        return Check("Agents", "Specialists", FAIL,
                     f"{len(loaded)}/{len(AGENT_MODULES)}  "
                     + ", ".join(broken[:2]))
    return Check("Agents", "Specialists", OK,
                 f"{len(loaded)}/{len(AGENT_MODULES)} loaded")


def _check_registry():
    try:
        # ensure agents register
        for _, mod in AGENT_MODULES:
            try:
                importlib.import_module(mod)
            except Exception:
                pass
        from ..core.registry import registry
        reg = registry()
        health = reg.health()
        bad = [h["name"] for h in health if not h["ok"]]
        if bad:
            return Check("Agents", "Registry", WARN,
                         f"unhealthy: {', '.join(bad)}")
        return Check("Agents", "Registry", OK, f"{len(health)} registered")
    except Exception as e:
        return Check("Agents", "Registry", FAIL,
                     f"{type(e).__name__}: {e}")


def _check_orchestrator():
    try:
        from ..core.orchestrator import orchestrator
        o = orchestrator()
        r = o.route("list_tasks", actor="diag")
        if not r.get("ok"):
            return Check("Agents", "Orchestrator", WARN,
                         r.get("reason", "")[:50])
        return Check("Agents", "Orchestrator", OK,
                     f"route ok via {r.get('specialist')}")
    except Exception as e:
        return Check("Agents", "Orchestrator", FAIL,
                     f"{type(e).__name__}: {e}")


# ─────────────── section: SYSTEM ───────────────

def _check_disk():
    try:
        u = shutil.disk_usage(str(BASE_DIR))
        free_mb = u.free // (1024 * 1024)
        if free_mb < 50:
            return Check("System", "Disk space", WARN, f"{free_mb} MB free")
        return Check("System", "Disk space", OK, f"{free_mb} MB free")
    except Exception as e:
        return Check("System", "Disk space", WARN,
                     f"{type(e).__name__}: {e}")


def _check_upgrade_lab():
    try:
        from ..upgrade import proposal, apply as A
        pend = len(proposal.pending())
        snaps = len(A.list_snapshots())
        if pend > 10:
            return Check("System", "Upgrade Lab", WARN,
                         f"{pend} pending, {snaps} snapshots")
        return Check("System", "Upgrade Lab", OK,
                     f"{pend} pending, {snaps} snapshots")
    except Exception as e:
        return Check("System", "Upgrade Lab", WARN,
                     f"{type(e).__name__}: {e}")


# ─────────────── section: AGENTS ───────────────

AGENT_MODULES = [
    ("pa", "mimi.agents.pa"),
    ("manager", "mimi.agents.manager"),
    ("accountant", "mimi.agents.accountant"),
    ("civil", "mimi.agents.civil"),
    ("legal", "mimi.agents.legal"),
    ("advisor", "mimi.agents.advisor"),
]


def _check_agents():
    loaded = []
    broken = []
    for name, mod in AGENT_MODULES:
        try:
            importlib.import_module(mod)
            loaded.append(name)
        except Exception as e:
            broken.append(f"{name}: {type(e).__name__}")
    if broken:
        return Check("Agents", "Specialists", FAIL,
                     f"{len(loaded)}/{len(AGENT_MODULES)}  "
                     + ", ".join(broken[:2]))
    return Check("Agents", "Specialists", OK,
                 f"{len(loaded)}/{len(AGENT_MODULES)} loaded")


def _check_registry():
    try:
        # ensure agents register
        for _, mod in AGENT_MODULES:
            try:
                importlib.import_module(mod)
            except Exception:
                pass
        from ..core.registry import registry
        reg = registry()
        health = reg.health()
        bad = [h["name"] for h in health if not h["ok"]]
        if bad:
            return Check("Agents", "Registry", WARN,
                         f"unhealthy: {', '.join(bad)}")
        return Check("Agents", "Registry", OK, f"{len(health)} registered")
    except Exception as e:
        return Check("Agents", "Registry", FAIL,
                     f"{type(e).__name__}: {e}")


def _check_orchestrator():
    try:
        from ..core.orchestrator import orchestrator
        o = orchestrator()
        r = o.route("list_tasks", actor="diag")
        if not r.get("ok"):
            return Check("Agents", "Orchestrator", WARN,
                         r.get("reason", "")[:50])
        return Check("Agents", "Orchestrator", OK,
                     f"route ok via {r.get('specialist')}")
    except Exception as e:
        return Check("Agents", "Orchestrator", FAIL,
                     f"{type(e).__name__}: {e}")


# ─────────────── section: SYSTEM ───────────────

def _check_disk():
    try:
        u = shutil.disk_usage(str(BASE_DIR))
        free_mb = u.free // (1024 * 1024)
        if free_mb < 50:
            return Check("System", "Disk space", WARN, f"{free_mb} MB free")
        return Check("System", "Disk space", OK, f"{free_mb} MB free")
    except Exception as e:
        return Check("System", "Disk space", WARN,
                     f"{type(e).__name__}: {e}")


def _check_upgrade_lab():
    try:
        from ..upgrade import proposal, apply as A
        pend = len(proposal.pending())
        snaps = len(A.list_snapshots())
        if pend > 10:
            return Check("System", "Upgrade Lab", WARN,
                         f"{pend} pending, {snaps} snapshots")
        return Check("System", "Upgrade Lab", OK,
                     f"{pend} pending, {snaps} snapshots")
    except Exception as e:
        return Check("System", "Upgrade Lab", WARN,
                     f"{type(e).__name__}: {e}")


# ─────────────── aggregator ───────────────

ALL_CHECKS = [
    _check_python, _check_curses, _check_core_modules,
    _check_db_exists, _check_tables, _check_required_tables,
    _check_integrity,
    _check_trust_root, _check_key_perms, _check_audit_chain,
    _check_permissions, _check_no_refuse_bypass,
    _check_agents, _check_registry, _check_orchestrator,
    _check_disk, _check_upgrade_lab,
]


def run_all():
    start = time.time()
    checks = []
    for fn in ALL_CHECKS:
        try:
            c = fn()
        except Exception as e:
            c = Check("Unknown", fn.__name__, FAIL,
                      f"{type(e).__name__}: {e}")
        checks.append(c)

    ok = sum(1 for c in checks if c.status == OK)
    warn = sum(1 for c in checks if c.status == WARN)
    fail = sum(1 for c in checks if c.status == FAIL)

    # group
    sections = {}
    for c in checks:
        sections.setdefault(c.section, []).append(c)

    return {
        "ok": ok, "warn": warn, "fail": fail,
        "total": len(checks),
        "elapsed_sec": round(time.time() - start, 3),
        "sections": {k: [c.dict() for c in v] for k, v in sections.items()},
        "checks": [c.dict() for c in checks],
    }


# ─────────────── CLI ───────────────

def _print_report(r):
    print()
    print("=" * 60)
    print("  MIMI SUPER SONIC DIAGNOSTIC")
    print("=" * 60)
    print(f"  OK {r['ok']}   WARN {r['warn']}   FAIL {r['fail']}   "
          f"({r['elapsed_sec']}s)")
    print("-" * 60)
    for section, items in r["sections"].items():
        print(f"\n  [{section}]")
        for it in items:
            mark = "OK " if it["status"] == OK else \
                   "!  " if it["status"] == WARN else "X  "
            print(f"    {mark} {it['name']:<22} {it['detail'][:40]}")
    print()
    print("=" * 60)


def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        r = run_all()
        _print_report(r)
        return 0 if r["fail"] == 0 else 1
    if cmd == "json":
        import json
        print(json.dumps(run_all(), indent=2))
        return 0
    print("usage: python -m mimi.health.diagnostic [run|json]")
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
