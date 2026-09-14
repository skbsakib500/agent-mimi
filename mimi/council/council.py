"""Council - the body of departments.

Registers all departments, routes commands across them, and provides
a single point for Nusrat to talk to.
"""
from ..guardian import audit
from .department import Department


class Council:
    def __init__(self):
        self._depts = {}

    def register(self, dept):
        if not isinstance(dept, Department):
            raise TypeError("not a Department")
        self._depts[dept.NAME] = dept
        audit.log("dept_registered", actor="council",
                  payload={"name": dept.NAME, "role": dept.ROLE})
        return dept

    def unregister(self, name):
        self._depts.pop(name, None)

    def get(self, name):
        return self._depts.get(name)

    def all(self):
        return sorted(self._depts.values(), key=lambda d: d.PRIORITY)

    def find_by_capability(self, cap):
        cap = str(cap).lower()
        matches = []
        for d in self._depts.values():
            caps = [c.lower() for c in d.CAPABILITIES]
            if cap in caps:
                matches.append(d)
        matches.sort(key=lambda d: d.PRIORITY)
        return matches

    def route(self, command, args=None, actor="system"):
        """Route to the first department that claims this command."""
        args = args or {}
        self._unhandled = getattr(self, "_unhandled", [])
        # capability lookup
        cap = self._cap_for(command)
        candidates = self.find_by_capability(cap)

        # fallback: try each dept's handle()
        tried = []
        for d in candidates:
            try:
                result = d.handle(command, args, actor=actor)
                audit.log("council_routed", actor="council",
                          payload={"cmd": command, "dept": d.NAME})
                return {"ok": True, "dept": d.NAME, "result": result}
            except NotImplementedError:
                tried.append(d.NAME)
            except Exception as e:
                audit.log("council_error", actor="council",
                          payload={"cmd": command, "dept": d.NAME,
                                   "err": f"{type(e).__name__}: {e}"})
                return {"ok": False, "dept": d.NAME,
                        "reason": f"{type(e).__name__}: {e}"}
        self._unhandled = getattr(self, "_unhandled", [])
        if command not in self._unhandled:
            self._unhandled.append(command)
        audit.log("council_unhandled", actor="council",
                  payload={"cmd": command})
        return {"ok": False,
                "reason": f"no department handles '{command}'",
                "tried": tried}

    def unhandled_commands(self):
        return list(getattr(self, "_unhandled", []))

    def suggest_new_department(self):
        """Return a draft proposal for the most frequent unhandled command."""
        cmds = self.unhandled_commands()
        if not cmds:
            return None
        cmd = cmds[0]
        from . import factory
        return factory.propose_new(
            name=cmd.replace("-", "_")[:30],
            role="custom",
            mandate=f"auto-created to handle '{cmd}'",
            capabilities=[cmd],
            proposer="Mimi/auto")

    def _cap_for(self, command):
        return command  # default: command == capability

    def health(self):
        return [d.health() for d in self.all()]

    def describe_all(self):
        return [d.describe() for d in self.all()]


_COUNCIL = Council()


def council():
    return _COUNCIL
