"""V10 Core - module registry.

Each specialist registers itself at import time. The orchestrator
consults the registry to route events / commands.
"""
from ..guardian import audit


class Registry:
    def __init__(self):
        self._modules = {}

    def register(self, name, obj, *, role=None, capabilities=None,
                 description=""):
        self._modules[name] = {
            "name": name,
            "obj": obj,
            "role": role or "generic",
            "capabilities": list(capabilities or []),
            "description": description,
        }
        audit.log("module_registered", actor="registry",
                  payload={"name": name, "role": role or "generic"})
        return obj

    def unregister(self, name):
        self._modules.pop(name, None)

    def get(self, name):
        entry = self._modules.get(name)
        return entry["obj"] if entry else None

    def info(self, name):
        return self._modules.get(name)

    def all(self):
        return list(self._modules.values())

    def find_by_capability(self, cap):
        cap = cap.lower()
        return [m for m in self._modules.values()
                if cap in [c.lower() for c in m["capabilities"]]]

    def health(self):
        out = []
        for m in self._modules.values():
            obj = m["obj"]
            # A module is healthy if it has callable handle() OR
            # callable main() OR it's a plain dict of functions
            ok = False
            if hasattr(obj, "handle") and callable(getattr(obj, "handle")):
                ok = True
            elif hasattr(obj, "main") and callable(getattr(obj, "main")):
                ok = True
            elif isinstance(obj, dict) and any(callable(v) for v in obj.values()):
                ok = True
            out.append({"name": m["name"], "role": m["role"],
                        "ok": ok, "capabilities": m["capabilities"]})
        return out


_REG = Registry()


def registry():
    return _REG
