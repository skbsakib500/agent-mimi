"""Council - Department base class.

A department is a persistent brain with:
  - role, mandate, capabilities
  - private memory
  - the ability to spawn Workers for individual tasks
  - reporting duty to Nusrat
"""
from datetime import datetime
from . import memory as mem
from ..guardian import audit


class Worker:
    """Ephemeral - spawned per task, dies after."""
    def __init__(self, parent_dept, task):
        self.dept = parent_dept
        self.task = task
        self.started = datetime.now()
        self.result = None
        self.error = None

    def run(self, fn):
        try:
            self.result = fn()
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
        return self.result

    def dict(self):
        return {
            "dept": self.dept,
            "task": self.task,
            "started": self.started.isoformat(timespec="seconds"),
            "result": self.result,
            "error": self.error,
        }


class Department:
    NAME = "generic"
    ROLE = "generic"
    MANDATE = "generic department"
    CAPABILITIES = ()
    PRIORITY = 5         # 1=highest, 10=lowest

    def __init__(self):
        self.workers = []

    # ── dispatch ──
    def handle(self, command, args=None, actor="system"):
        """Handle a command. Return dict. May raise."""
        raise NotImplementedError(
            f"{self.NAME} cannot handle '{command}'")

    # ── memory helpers ──
    def remember(self, kind, value, key=None, importance=5):
        mem.remember(self.NAME, kind, value, key, importance)

    def recall(self, kind=None, limit=20):
        return mem.recall(self.NAME, kind, limit)

    # ── workers ──
    def spawn(self, task, fn):
        w = Worker(self.NAME, task)
        self.workers.append(w)
        audit.log("worker_spawned", actor=self.NAME,
                  payload={"task": task})
        return w.run(fn)

    # ── health ──
    def health(self):
        mem_count = 0
        try:
            mem_count = len(self.recall(limit=1000))
        except Exception:
            pass
        return {
            "name": self.NAME,
            "role": self.ROLE,
            "capabilities": list(self.CAPABILITIES),
            "priority": self.PRIORITY,
            "memory_items": mem_count,
            "workers_run": len(self.workers),
            "ok": True,
        }

    # ── self-description ──
    def describe(self):
        return {
            "name": self.NAME,
            "role": self.ROLE,
            "mandate": self.MANDATE,
            "capabilities": list(self.CAPABILITIES),
            "priority": self.PRIORITY,
        }
