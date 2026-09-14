"""Department Factory - auto-create new departments.

Flow:
  1. propose_new(name, role, mandate, capabilities)
     -> creates a proposal in upgrade_proposals + draft file in sandbox
  2. test_draft(proposal_id)
     -> imports the draft in isolation
  3. approve_and_install(proposal_id, approved_by)
     -> copies draft into mimi/council/departments/ + registers
  4. reject(proposal_id) -> cleanup

Never overwrites an existing department file.
"""
import importlib
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from ..database import BASE_DIR, execute
from ..guardian import audit
from ..guardian.permissions import check
from ..upgrade import proposal as prop_mod

FACTORY_DIR = Path.home() / ".mimi" / "factory"
DEPT_DIR = Path(BASE_DIR) / "mimi" / "council" / "departments"

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,30}$")


def _ensure():
    FACTORY_DIR.mkdir(parents=True, exist_ok=True)


def _validate_name(name):
    if not NAME_RE.match(name or ""):
        raise ValueError(
            "name must be lowercase letters/digits/underscore, 2-31 chars"
        )
    if (DEPT_DIR / f"{name}.py").exists():
        raise ValueError(f"department '{name}' already exists")
    return name


def _template(name, cls_name, role, mandate, caps):
    caps_repr = ", ".join(f'"{c}"' for c in caps)
    return f'''"""Auto-generated department: {name}."""
from datetime import date
from ..department import Department
from ...database import fetch_one, fetch_all, execute
from ...guardian import audit


class {cls_name}(Department):
    NAME = "{name}"
    ROLE = "{role}"
    MANDATE = "{mandate}"
    CAPABILITIES = ({caps_repr})
    PRIORITY = 5

    def handle(self, command, args=None, actor="system"):
        args = args or {{}}
        table = {{
            "{name}_ping": self._ping,
            "{name}_echo": self._echo,
        }}
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"{cls_name} cannot handle '{{command}}'")
        return fn(args, actor)

    def _ping(self, args, actor):
        return {{"ok": True, "dept": self.NAME, "pong": True}}

    def _echo(self, args, actor):
        msg = (args.get("message") or "").strip()
        return {{"ok": True, "echo": msg}}
'''


def _cls_name(name):
    return "".join(p.capitalize() for p in name.split("_")) or "Custom"


def propose_new(name, role, mandate, capabilities, proposer="SKB Sakib"):
    """Create a draft + upgrade_proposals entry. Does NOT install."""
    _ensure()
    name = _validate_name(name)
    if not role or not mandate:
        raise ValueError("role and mandate required")
    caps = [c.strip() for c in (capabilities or []) if c.strip()]
    if not caps:
        raise ValueError("at least one capability required")

    cls_name = _cls_name(name)
    draft_path = FACTORY_DIR / f"{name}.py"
    draft_path.write_text(
        _template(name, cls_name, role, mandate, caps),
        encoding="utf-8")

    pid = prop_mod.create(
        category="department",
        module=name,
        problem=f"new department requested: {name}",
        proposal=f"install {name} (role={role}, caps={len(caps)})",
        risk_level="medium",
        files=[str(draft_path)],
    )
    audit.log("factory_proposed", actor=proposer,
              payload={"name": name, "role": role, "caps": len(caps),
                       "pid": pid})
    return {"ok": True, "proposal_id": pid,
            "draft_path": str(draft_path),
            "class": cls_name, "caps": caps}


def test_draft(proposal_id):
    """Import the draft module in isolation (sandbox)."""
    p = prop_mod.get(proposal_id)
    if not p:
        raise ValueError("proposal not found")
    files = p.get("files_changed") or []
    if not files:
        raise ValueError("no draft file linked to proposal")
    src = Path(files[0])
    if not src.exists():
        raise FileNotFoundError(f"draft not found: {src}")

    # Snapshot state
    old_path = list(sys.path)
    old_modules = dict(sys.modules)

    # Copy draft into a temp package so relative imports work
    box = FACTORY_DIR / f"_test_{int(proposal_id)}"
    if box.exists():
        shutil.rmtree(box, ignore_errors=True)
    # We only need mimi.council.departments on path for relative import test
    test_pkg = box / "mimi" / "council" / "departments"
    test_pkg.mkdir(parents=True, exist_ok=True)
    (box / "mimi" / "__init__.py").touch()
    (box / "mimi" / "council" / "__init__.py").touch()
    (box / "mimi" / "council" / "departments" / "__init__.py").touch()
    shutil.copy2(src, test_pkg / src.name)

    result = {"ok": False, "error": None, "class": None}
    try:
        sys.path.insert(0, str(box))
        # unload
        for n in list(sys.modules.keys()):
            if n == "mimi" or n.startswith("mimi."):
                sys.modules.pop(n, None)
        mod = importlib.import_module(
            f"mimi.council.departments.{src.stem}")
        # find the Department subclass
        from ..council.department import Department
        cls = None
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and issubclass(obj, Department) \
                    and obj is not Department:
                cls = obj
                break
        if cls is None:
            result["error"] = "no Department subclass found"
        else:
            inst = cls()
            r = inst.handle(f"{inst.NAME}_ping", {})
            if not r.get("ok"):
                result["error"] = f"ping failed: {r}"
            else:
                result["ok"] = True
                result["class"] = cls.__name__
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    finally:
        sys.path[:] = old_path
        for n in list(sys.modules.keys()):
            if n == "mimi" or n.startswith("mimi."):
                sys.modules.pop(n, None)
        sys.modules.update(
            {k: v for k, v in old_modules.items()
             if k == "mimi" or k.startswith("mimi.")})
        shutil.rmtree(box, ignore_errors=True)

    audit.log("factory_tested", actor="factory",
              payload={"pid": int(proposal_id), "ok": result["ok"],
                       "error": result["error"]})
    return result


def install_draft(proposal_id, approved_by=None, actor="factory"):
    """Move draft into production departments + register. Owner-gated."""
    ok, reason = check("write_code", actor=actor,
                       approved_by=approved_by)
    if not ok:
        return {"ok": False, "reason": reason}

    p = prop_mod.get(proposal_id)
    if not p:
        return {"ok": False, "reason": "proposal not found"}
    files = p.get("files_changed") or []
    if not files:
        return {"ok": False, "reason": "no draft linked"}
    src = Path(files[0])
    if not src.exists():
        return {"ok": False, "reason": f"draft missing: {src}"}

    name = src.stem
    dst = DEPT_DIR / f"{name}.py"
    if dst.exists():
        return {"ok": False, "reason":
                f"department file exists: {dst.name}"}

    # copy
    try:
        shutil.copy2(src, dst)
    except Exception as e:
        return {"ok": False, "reason": f"copy failed: {e}"}

    # register at runtime
    try:
        for n in list(sys.modules.keys()):
            if n.startswith("mimi.council.departments."):
                sys.modules.pop(n, None)
        mod = importlib.import_module(f"mimi.council.departments.{name}")
        from ..council.council import council
        from ..council.department import Department
        cls = None
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and issubclass(obj, Department) \
                    and obj is not Department:
                cls = obj
                break
        if cls is None:
            raise RuntimeError("no Department subclass in installed file")
        council().register(cls())
    except Exception as e:
        # rollback file
        dst.unlink(missing_ok=True)
        return {"ok": False, "reason":
                f"register failed: {type(e).__name__}: {e}"}

    audit.log("factory_installed", actor=actor,
              payload={"pid": int(proposal_id), "name": name,
                       "file": str(dst)})
    return {"ok": True, "name": name, "file": str(dst)}


def reject_draft(proposal_id, actor="factory"):
    p = prop_mod.get(proposal_id)
    if not p:
        return {"ok": False, "reason": "not found"}
    files = p.get("files_changed") or []
    for f in files:
        try:
            Path(f).unlink(missing_ok=True)
        except Exception:
            pass
    prop_mod.transition(proposal_id, "REJECTED", actor=actor)
    audit.log("factory_rejected", actor=actor,
              payload={"pid": int(proposal_id)})
    return {"ok": True}


def list_drafts():
    _ensure()
    out = []
    for f in sorted(FACTORY_DIR.glob("*.py")):
        if f.stem.startswith("_"):
            continue
        out.append(f)
    return out


def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        for f in list_drafts():
            print(f"  {f.name}")
        return
    if cmd == "propose":
        if len(sys.argv) < 5:
            print("usage: propose <name> <role> <mandate> <cap1,cap2>")
            return
        name, role, mandate, caps = sys.argv[2:6]
        r = propose_new(name, role, mandate, caps.split(","))
        print("  OK", r)
        return
    if cmd == "test":
        if len(sys.argv) < 3:
            print("usage: test <pid>"); return
        print("  ", test_draft(sys.argv[2]))
        return
    if cmd == "install":
        if len(sys.argv) < 3:
            print("usage: install <pid>"); return
        print("  ", install_draft(sys.argv[2], approved_by="SKB Sakib"))
        return
    if cmd == "reject":
        if len(sys.argv) < 3:
            print("usage: reject <pid>"); return
        print("  ", reject_draft(sys.argv[2]))
        return
    print("usage: list | propose ... | test <pid> | install <pid> | reject <pid>")


if __name__ == "__main__":
    main()
