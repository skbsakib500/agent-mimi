"""DevOps department - Mimi's self-maintenance, backups, sync."""
from datetime import datetime
from pathlib import Path
from ..department import Department
from ...database import BASE_DIR, get_tables
from ...guardian import audit


class DevOps(Department):
    NAME = "devops"
    ROLE = "site_reliability"
    MANDATE = "Backups, sync, health, upgrades, self-maintenance"
    CAPABILITIES = ("devops", "backup", "sync", "health",
                    "upgrade", "maintenance")
    PRIORITY = 1

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "backup_now":     self._backup,
            "sync_status":    self._sync_status,
            "sync_push":      self._sync_push,
            "sync_pull":      self._sync_pull,
            "disk_usage":     self._disk,
            "system_health":  self._health,
            "run_cycle":      self._cycle,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"DevOps cannot handle '{command}'")
        return fn(args, actor)

    def _backup(self, args, actor):
        try:
            from ...upgrade import apply as A
            code = A.snapshot_code(tag="dept_backup")
            db = A.snapshot_db(tag="dept_backup")
            return {"ok": True, "code": str(code), "db": str(db)}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def _sync_status(self, args, actor):
        try:
            from ...sync import full_status
            return full_status()
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}

    def _sync_push(self, args, actor):
        try:
            from ...sync import push
            ok, msg = push()
            return {"ok": ok, "message": str(msg)[:200]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _sync_pull(self, args, actor):
        try:
            from ...sync import pull
            ok, msg = pull()
            return {"ok": ok, "message": str(msg)[:200]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _disk(self, args, actor):
        try:
            import shutil
            u = shutil.disk_usage(str(BASE_DIR))
            return {
                "total_mb": u.total // (1024 * 1024),
                "used_mb": u.used // (1024 * 1024),
                "free_mb": u.free // (1024 * 1024),
            }
        except Exception as e:
            return {"error": str(e)}

    def _health(self, args, actor):
        try:
            from ...health.diagnostic import run_all
            r = run_all()
            return {"ok": r["ok"], "warn": r["warn"],
                    "fail": r["fail"], "total": r["total"]}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}

    def _cycle(self, args, actor):
        try:
            from ...upgrade import lab
            s = lab.run_full_cycle(actor="devops")
            return {"steps": len(s["steps"]),
                    "applied": len(s.get("applied", [])),
                    "rolled_back": len(s.get("rolled_back", [])),
                    "errors": len(s.get("errors", []))}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}
