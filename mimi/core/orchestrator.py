"""V10 Core - orchestrator.

The brain. Receives commands, consults the registry, dispatches to
specialists via the bus, enforces permission gate, records results.
"""
from .bus import bus
from .registry import registry
from ..guardian import audit
from ..guardian.permissions import check
from ..trust.loader import ensure_trusted


class Orchestrator:
    def __init__(self):
        self.bus = bus()
        self.registry = registry()
        self.history = []

    def route(self, command, args=None, actor="system",
              approved_by=None):
        """Route a command to the right specialist.

        Returns dict: {ok, specialist, result, reason}.
        """
        args = args or {}

        if not ensure_trusted(fail_closed=False):
            return {"ok": False, "reason": "trust root not verified"}

        # Determine which specialist should handle this
        spec = self._pick_specialist(command)
        if spec is None:
            audit.log("route_no_specialist", actor=actor,
                      payload={"command": command})
            return {"ok": False, "reason": f"no specialist for '{command}'"}

        # Permission gate
        op = self._op_for(command)
        allowed, reason = check(op, actor=actor, approved_by=approved_by,
                                 context={"command": command, "spec": spec})
        if not allowed:
            return {"ok": False, "specialist": spec, "reason": reason}

        # Dispatch
        self.bus.publish(f"command.{command}",
                         actor=actor,
                         payload={"args": args, "spec": spec})
        self.bus.drain()

        handler = self.registry.get(spec)
        result = None
        try:
            if handler is None:
                raise RuntimeError(f"specialist '{spec}' not registered")
            if hasattr(handler, "handle"):
                result = handler.handle(command, args, actor=actor)
            elif hasattr(handler, "main"):
                result = handler.main(command, args)
            elif isinstance(handler, dict) and command in handler:
                result = handler[command](args)
            else:
                raise RuntimeError(
                    f"specialist '{spec}' has no dispatchable entry")
        except Exception as e:
            audit.log("specialist_error", actor="orch",
                      payload={"spec": spec, "command": command,
                               "error": f"{type(e).__name__}: {e}"})
            return {"ok": False, "specialist": spec,
                    "reason": f"{type(e).__name__}: {e}"}

        rec = {"command": command, "spec": spec, "actor": actor,
               "ok": True, "result": result}
        self.history.append(rec)
        audit.log("route_ok", actor="orch",
                  payload={"spec": spec, "command": command})
        return {"ok": True, "specialist": spec, "result": result}

    def _pick_specialist(self, command):
        cap = self._cap_for(command)
        matches = self.registry.find_by_capability(cap)
        if matches:
            return matches[0]["name"]
        return None

    def _cap_for(self, command):
        # map command -> capability keyword
        table = {
            "add_task": "tasks", "list_tasks": "tasks",
            "complete_task": "tasks",
            "add_goal": "goals", "list_goals": "goals",
            "add_expense": "finance", "add_income": "finance",
            "add_debt": "finance", "balance": "finance",
            "study_log": "study", "study_summary": "study",
            "journal_add": "journal",
            "boq": "civil", "estimate": "civil", "quantity": "civil",
            "legal_lookup": "legal", "legal_draft": "legal",
            "advice": "advisor", "plan": "advisor",
            "brief": "pa", "schedule": "pa", "notes": "pa",
        }
        return table.get(command, command)

    def _op_for(self, command):
        if command.startswith("list_") or command in (
                "balance", "study_summary", "brief", "plan", "advice"):
            return "read"
        if command.startswith("delete_") or command == "reset":
            return "delete_record"
        return "write_db"

    def stats(self):
        return {
            "history": len(self.history),
            "registry": [m["name"] for m in self.registry.all()],
            "bus": self.bus.stats(),
        }


_ORCH = Orchestrator()


def orchestrator():
    return _ORCH
