"""Plugin system - auto-discovers mimi/plugins/*.py."""
import importlib, importlib.util, inspect, sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent / "plug_store"

_cache = {}


def _ensure_dir():
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    init = PLUGIN_DIR / "__init__.py"
    if not init.exists():
        init.write_text('"""User plugins live here."""\n')


def discover():
    """Return list of plugin metadata dicts (loaded lazily)."""
    _ensure_dir()
    out = []
    for f in sorted(PLUGIN_DIR.glob("*.py")):
        if f.stem.startswith("_"):
            continue
        name = f.stem
        mod_name = f"mimi.plug_store.{name}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, f)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)
            _cache[name] = mod

            meta = {
                "name": getattr(mod, "PLUGIN_NAME", name),
                "description": getattr(mod, "PLUGIN_DESCRIPTION", ""),
                "version": getattr(mod, "PLUGIN_VERSION", "0.1"),
                "author": getattr(mod, "PLUGIN_AUTHOR", ""),
                "path": str(f),
                "module": mod,
            }
            has_run = (callable(getattr(mod, "main", None))
                       or callable(getattr(mod, "run", None)))
            meta["runnable"] = has_run
            out.append(meta)
        except Exception as e:
            out.append({
                "name": name,
                "description": f"[ERROR] {type(e).__name__}: {e}",
                "version": "?",
                "author": "",
                "path": str(f),
                "module": None,
                "runnable": False,
                "error": str(e),
            })
    return out


def run_plugin(name):
    meta = None
    for m in discover():
        if m["name"] == name or Path(m["path"]).stem == name:
            meta = m
            break
    if not meta:
        return False, "not found"
    if not meta.get("runnable"):
        return False, "not runnable"
    mod = meta["module"]
    fn = getattr(mod, "main", None) or getattr(mod, "run", None)
    if not callable(fn):
        return False, "no callable entry"
    try:
        fn()
        return True, "OK"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def template():
    return '''"""Example plugin for Agent Mimi.

Drop a .py file into mimi/plugins/ with at least one of:
  PLUGIN_NAME = "My Plugin"
  def main(): ...   (or)   run = main
"""

PLUGIN_NAME = "Hello Plugin"
PLUGIN_DESCRIPTION = "Says hello"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "You"


def main():
    from mimi.ui import c, GREEN, clear, header, pause
    clear()
    header("HELLO PLUGIN", "Loaded from mimi/plugins/")
    print(c("\\n  Hello from a plugin!\\n", GREEN))
    pause()


run = main
'''


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    while True:
        clear()
        header("🧩 PLUGINS", f"Folder: {PLUGIN_DIR}")
        items = discover()
        if not items:
            print(c("\n  No plugins found.", YELLOW))
            print("  Drop a .py into mimi/plugins/ — it will appear here.")
        else:
            section(f"FOUND {len(items)}", "📦")
            for i, p in enumerate(items, 1):
                mark = c("●", GREEN) if p.get("runnable") else c("○", RED)
                print(f"  {i}. {mark} {p['name']}  v{p['version']}")
                if p["description"]:
                    print(c(f"      {p['description']}", DIM + WHITE))
                if p.get("error"):
                    print(c(f"      X {p['error']}", RED))
        print()
        print("  1. Run plugin")
        print("  2. Show template")
        print("  3. Open plugins folder path")
        print("  0. Back")
        ch = input(c("\n  > Select: ")).strip()
        if ch == "0":
            break
        elif ch == "1":
            if not items:
                print(c("  X None available.", RED)); pause(); continue
            try:
                idx = int(input("  #: ").strip()) - 1
                if 0 <= idx < len(items):
                    ok, msg = run_plugin(items[idx]["name"])
                    if not ok:
                        print(c(f"  X {msg}", RED)); pause()
                else:
                    print(c("  X Invalid.", RED)); pause()
            except ValueError:
                print(c("  X Invalid.", RED)); pause()
        elif ch == "2":
            clear()
            header("PLUGIN TEMPLATE", "Copy into mimi/plugins/")
            print(template())
            pause()
        elif ch == "3":
            print(c(f"\n  {PLUGIN_DIR}", CYAN))
            pause()

run = main
