"""Agent Mimi - module router."""
from importlib import import_module
import inspect

GENERIC = ("main", "run", "cli", "start")

def _zero_arg(fn):
    try: sig = inspect.signature(fn)
    except (TypeError, ValueError): return False
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD): continue
        if p.default is inspect.Parameter.empty: return False
    return True

def resolve(path, module=None):
    mod = module or import_module(path)
    for name in ("main", "run"):
        fn = getattr(mod, name, None)
        if callable(fn) and _zero_arg(fn): return fn, "standard", name
    for name in GENERIC:
        if name in ("main", "run"): continue
        fn = getattr(mod, name, None)
        if callable(fn) and _zero_arg(fn): return fn, "adapter", name
    return None, "missing", None

def run_module(path, pause_fn=None, error_fn=None):
    try:
        mod = import_module(path)
        fn, mode, name = resolve(path, mod)
        if fn is None:
            msg = f"{path} has no compatible entry point."
            if error_fn: error_fn(msg)
            elif pause_fn: print(msg); pause_fn()
            return False
        fn()
        return True
    except Exception as exc:
        msg = f"{path}: {type(exc).__name__}: {exc}"
        if error_fn: error_fn(msg)
        elif pause_fn: print(msg); pause_fn()
        return False

def health_check(categories):
    results = []
    for ck, cat in categories.items():
        for name, path in cat["items"]:
            try:
                mod = import_module(path)
                fn, mode, entry = resolve(path, mod)
                if fn is None:
                    status, detail = "MISSING", "No zero-arg entry point."
                else:
                    status = "PASS" if mode == "standard" else "ADAPTER"
                    detail = "Ready"
                results.append({"category": ck, "name": name, "path": path,
                                "status": status, "mode": mode,
                                "entrypoint": entry or "", "detail": detail})
            except Exception as exc:
                results.append({"category": ck, "name": name, "path": path,
                                "status": "IMPORT ERROR", "mode": "",
                                "entrypoint": "",
                                "detail": f"{type(exc).__name__}: {exc}"})
    return results
