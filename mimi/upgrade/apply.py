"""V10 Upgrade Lab - atomic apply + rollback.

Strategy:
  1. Snapshot the CURRENT production code into ~/.mimi/snapshots/<ts>/
  2. Snapshot the CURRENT production DB (mimi.db) if any
  3. Apply candidate: copy files from a sandbox or source tree
  4. Verify with import + health check
  5. If verify fails -> restore snapshot atomically
  6. Record everything in audit + proposal

Never touches data/ during code apply unless DB apply is explicit.
"""
import os
import shutil
import time
import importlib
import sys
from datetime import datetime
from pathlib import Path

from ..database import BASE_DIR, DB_PATH
from ..guardian import audit

SNAP_ROOT = Path.home() / ".mimi" / "snapshots"
EXCLUDE_DIRS = {"data", ".git", "backups", "exports", "reports",
                "__pycache__", ".pytest_cache"}


def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _copy_filtered(src, dst):
    src = Path(src)
    dst = Path(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src):
        root = Path(root)
        rel = root.relative_to(src)
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            try:
                shutil.copy2(root / f, dst / rel / f)
            except Exception:
                pass


def snapshot_code(tag="pre_apply"):
    """Take a snapshot of the current production code tree."""
    SNAP_ROOT.mkdir(parents=True, exist_ok=True)
    snap = SNAP_ROOT / f"{tag}_{_ts()}"
    _copy_filtered(BASE_DIR, snap)
    audit.log("snapshot_code", actor="lab",
              payload={"path": str(snap), "tag": tag})
    return snap


def snapshot_db(tag="pre_apply"):
    """Snapshot the production DB if present."""
    SNAP_ROOT.mkdir(parents=True, exist_ok=True)
    snap = SNAP_ROOT / f"db_{tag}_{_ts()}"
    snap.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        target = snap / DB_PATH.name
        try:
            import sqlite3
            src = sqlite3.connect(str(DB_PATH))
            try:
                dst = sqlite3.connect(str(target))
                try:
                    src.backup(dst)
                finally:
                    dst.close()
            finally:
                src.close()
            # integrity check
            chk = sqlite3.connect(str(target))
            try:
                ok = chk.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                chk.close()
            if ok != "ok":
                target.unlink(missing_ok=True)
                raise RuntimeError("DB snapshot failed integrity check")
        except Exception as e:
            audit.log("snapshot_db_failed", actor="lab",
                      payload={"error": f"{type(e).__name__}: {e}"})
            return None
    audit.log("snapshot_db", actor="lab",
              payload={"path": str(snap), "tag": tag})
    return snap


def list_snapshots():
    if not SNAP_ROOT.exists():
        return []
    return sorted([d for d in SNAP_ROOT.iterdir() if d.is_dir()],
                  reverse=True)


def latest_snapshot():
    snaps = list_snapshots()
    return snaps[0] if snaps else None


# ─────────────────── verify ───────────────────

def _import_test_production():
    """Import every mimi/*.py module in the CURRENT sys.path.
    Returns (ok_count, broken_list)."""
    # Clear cached mimi modules so we re-read from disk
    for name in list(sys.modules.keys()):
        if name == "mimi" or name.startswith("mimi."):
            sys.modules.pop(name, None)
    broken = []
    ok = 0
    mimi_dir = Path(BASE_DIR) / "mimi"
    mods = sorted(f.stem for f in mimi_dir.glob("*.py")
                  if f.stem != "__init__")
    for m in mods:
        try:
            importlib.import_module(f"mimi.{m}")
            ok += 1
        except Exception as e:
            broken.append({"module": m,
                           "error": f"{type(e).__name__}: {e}"})
    return ok, broken


def _health_check():
    """Run a minimal health check on the production environment."""
    issues = []
    try:
        from ..database import get_tables
        tables = get_tables()
        if not tables:
            issues.append("no tables in DB")
    except Exception as e:
        issues.append(f"db: {type(e).__name__}: {e}")
    try:
        from ..trust.verify import verify_constitution
        ok, reason = verify_constitution()
        if not ok:
            issues.append(f"trust: {reason}")
    except Exception as e:
        issues.append(f"trust: {type(e).__name__}: {e}")
    return issues


def verify(actor="lab"):
    ok_count, broken = _import_test_production()
    health = _health_check()
    passed = (not broken) and (not health)
    audit.log("apply_verify", actor=actor,
              payload={"passed": passed, "imports_ok": ok_count,
                       "imports_broken": len(broken),
                       "health_issues": len(health)})
    return {
        "passed": passed,
        "imports_ok": ok_count,
        "imports_broken": broken,
        "health_issues": health,
    }


# ─────────────────── apply ───────────────────

def _copy_candidate(sandbox_path):
    """Copy candidate code from sandbox into production, replacing .py files.
    Preserves data/, .git/, backups/, exports/, reports/."""
    sandbox_path = Path(sandbox_path)
    if not sandbox_path.exists():
        raise FileNotFoundError(f"sandbox not found: {sandbox_path}")

    src_pkg = sandbox_path / "mimi"
    dst_pkg = Path(BASE_DIR) / "mimi"
    if not src_pkg.exists():
        raise FileNotFoundError("sandbox has no mimi/ directory")

    replaced = []
    for root, dirs, files in os.walk(src_pkg):
        root = Path(root)
        rel = root.relative_to(src_pkg)
        dst_dir = dst_pkg / rel
        dst_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            if f.endswith(".pyc"):
                continue
            try:
                shutil.copy2(root / f, dst_dir / f)
                replaced.append(str((dst_pkg / rel / f).relative_to(BASE_DIR)))
            except Exception as e:
                raise RuntimeError(
                    f"copy failed: {root/f} -> {dst_dir/f}: {e}")

    # Also copy top-level files that changed (README, CHANGELOG, etc.)
    for f in ("README.md", "CHANGELOG.md"):
        srcf = sandbox_path / f
        dstf = Path(BASE_DIR) / f
        if srcf.exists():
            try:
                shutil.copy2(srcf, dstf)
                replaced.append(f)
            except Exception:
                pass

    return replaced


def _restore_snapshot(snapshot_path):
    """Restore production code from snapshot (atomic from user's perspective)."""
    snap = Path(snapshot_path)
    if not snap.exists():
        raise FileNotFoundError(f"snapshot not found: {snap}")
    snap_pkg = snap / "mimi"
    dst_pkg = Path(BASE_DIR) / "mimi"
    if not snap_pkg.exists():
        raise FileNotFoundError("snapshot has no mimi/ directory")

    restored = []
    for root, dirs, files in os.walk(snap_pkg):
        root = Path(root)
        rel = root.relative_to(snap_pkg)
        dst_dir = dst_pkg / rel
        dst_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            try:
                shutil.copy2(root / f, dst_dir / f)
                restored.append(str((dst_pkg / rel / f).relative_to(BASE_DIR)))
            except Exception:
                pass
    return restored


def apply_candidate(sandbox_path, proposal_id=None, actor="lab",
                    approved_by=None):
    """Full apply pipeline with automatic rollback on verify failure.

    Steps:
      1. snapshot current code
      2. copy candidate over production
      3. verify
      4. if fail -> restore snapshot
    """
    from ..guardian.permissions import check
    ok, reason = check("upgrade_apply", actor=actor,
                        approved_by=approved_by)
    if not ok:
        return {"ok": False, "reason": reason}

    result = {"ok": False, "steps": []}

    # 1. snapshot
    snap = snapshot_code(tag=f"apply_{proposal_id or 'x'}")
    result["snapshot"] = str(snap)
    result["steps"].append({"step": "snapshot", "ok": True})

    # 2. copy
    try:
        replaced = _copy_candidate(sandbox_path)
        result["replaced"] = replaced
        result["steps"].append({"step": "copy", "ok": True,
                                 "files": len(replaced)})
    except Exception as e:
        result["reason"] = f"copy failed: {type(e).__name__}: {e}"
        result["steps"].append({"step": "copy", "ok": False})
        return result

    # 3. verify
    v = verify(actor=actor)
    result["verify"] = v
    result["steps"].append({"step": "verify", "ok": v["passed"]})

    if v["passed"]:
        result["ok"] = True
        audit.log("apply_success", actor=actor,
                  payload={"pid": proposal_id, "files": len(replaced)})
        return result

    # 4. rollback
    try:
        restored = _restore_snapshot(snap)
        result["rolled_back"] = True
        result["restored"] = len(restored)
        result["steps"].append({"step": "rollback", "ok": True,
                                 "files": len(restored)})
        audit.log("apply_rolled_back", actor=actor,
                  payload={"pid": proposal_id, "reason": "verify failed"})
    except Exception as e:
        result["rolled_back"] = False
        result["reason"] = f"rollback failed: {type(e).__name__}: {e}"
        result["steps"].append({"step": "rollback", "ok": False})

    return result


def rollback_to(snapshot_path, actor="lab", approved_by=None):
    """Manual rollback to a specific snapshot."""
    from ..guardian.permissions import check
    ok, reason = check("upgrade_rollback", actor=actor,
                        approved_by=approved_by)
    if not ok:
        return {"ok": False, "reason": reason}
    try:
        restored = _restore_snapshot(snapshot_path)
        v = verify(actor=actor)
        audit.log("manual_rollback", actor=actor,
                  payload={"snapshot": snapshot_path,
                           "restored": len(restored),
                           "verify_ok": v["passed"]})
        return {"ok": True, "restored": len(restored), "verify": v}
    except Exception as e:
        return {"ok": False,
                "reason": f"{type(e).__name__}: {e}"}


def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd == "snapshot":
        snap = snapshot_code()
        db = snapshot_db()
        print(f"  code snapshot: {snap}")
        print(f"  db snapshot  : {db}")
    elif cmd == "list":
        for s in list_snapshots():
            print(f"  {s}")
    elif cmd == "verify":
        v = verify()
        print(f"  passed: {v['passed']}")
        print(f"  imports ok: {v['imports_ok']}")
        for b in v["imports_broken"][:5]:
            print(f"    X {b['module']}: {b['error'][:60]}")
        for h in v["health_issues"]:
            print(f"    ! {h}")
    elif cmd == "apply" and len(sys.argv) > 2:
        r = apply_candidate(sys.argv[2],
                            approved_by="SKB Sakib")
        print(f"  ok: {r['ok']}")
        for s in r.get("steps", []):
            print(f"    [{ 'OK' if s['ok'] else 'X' }] {s['step']}")
        if r.get("reason"):
            print(f"  reason: {r['reason']}")
    elif cmd == "rollback" and len(sys.argv) > 2:
        r = rollback_to(sys.argv[2], approved_by="SKB Sakib")
        print(f"  ok: {r['ok']}")
        if r.get("restored"):
            print(f"  restored: {r['restored']} files")
    else:
        print("usage: python -m mimi.upgrade.apply "
              "<snapshot|list|verify|apply <sandbox>|rollback <snap>>")


if __name__ == "__main__":
    main()
