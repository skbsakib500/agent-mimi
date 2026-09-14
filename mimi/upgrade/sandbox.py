"""V10 Upgrade Lab - sandbox.

Never touches production. Every test runs inside a temp copy of the
code tree at ~/.mimi/sandbox/<proposal_id>/.

Design:
  - rsync-like copy of source tree (excluding data/, .git, backups)
  - import every module in isolation (sys.path switched)
  - run any registered test file (test_*.py)
  - return structured result, never raise
"""
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ..database import BASE_DIR
from ..guardian import audit

SANDBOX_ROOT = Path.home() / ".mimi" / "sandbox"
EXCLUDE_DIRS = {"data", ".git", "backups", "exports", "reports",
                "__pycache__", ".pytest_cache"}
EXCLUDE_SUFFIX = {".pyc", ".pyo"}


def _copy_tree(src, dst):
    """Simple filtered copy - skip excluded dirs and files."""
    src = Path(src)
    dst = Path(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src):
        root = Path(root)
        rel = root.relative_to(src)
        # prune dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            if Path(f).suffix in EXCLUDE_SUFFIX:
                continue
            try:
                shutil.copy2(root / f, dst / rel / f)
            except Exception:
                pass


def prepare(proposal_id):
    """Create a fresh sandbox copy for the given proposal."""
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    box = SANDBOX_ROOT / f"prop_{int(proposal_id)}"
    if box.exists():
        shutil.rmtree(box, ignore_errors=True)
    box.mkdir(parents=True, exist_ok=True)
    _copy_tree(BASE_DIR, box)
    audit.log("sandbox_prepared", actor="lab",
              payload={"pid": int(proposal_id), "path": str(box)})
    return box


def _isolated_import_test(box):
    """Import every mimi/*.py module with sandbox on sys.path[0]."""
    box = Path(box)
    pkg_root = box
    # Snapshot current
    old_path = list(sys.path)
    old_modules = dict(sys.modules)

    broken = []
    ok = 0
    try:
        sys.path.insert(0, str(pkg_root))
        # Unload any mimi.* modules so they re-import from sandbox
        for name in list(sys.modules.keys()):
            if name == "mimi" or name.startswith("mimi."):
                sys.modules.pop(name, None)

        mimi_dir = pkg_root / "mimi"
        mods = sorted(f.stem for f in mimi_dir.glob("*.py")
                      if f.stem != "__init__")
        for m in mods:
            name = f"mimi.{m}"
            try:
                importlib.import_module(name)
                ok += 1
            except Exception as e:
                broken.append({
                    "module": m,
                    "error": f"{type(e).__name__}: {e}",
                })
    finally:
        # Restore
        sys.path[:] = old_path
        for name in list(sys.modules.keys()):
            if name == "mimi" or name.startswith("mimi."):
                sys.modules.pop(name, None)
        sys.modules.update(
            {k: v for k, v in old_modules.items()
             if k == "mimi" or k.startswith("mimi.")})

    return {"ok": ok, "broken": broken}


def _run_test_files(box, timeout=60):
    """Run any test_*.py inside the sandbox using pytest if available,
    else run each file as a script."""
    box = Path(box)
    tests = list(box.rglob("test_*.py"))
    if not tests:
        return {"ran": 0, "passed": 0, "failed": 0, "details": []}

    results = []
    passed = failed = 0

    # Prefer pytest if importable
    pytest_ok = False
    try:
        import importlib.util
        pytest_ok = importlib.util.find_spec("pytest") is not None
    except Exception:
        pytest_ok = False

    for t in tests:
        entry = {"file": str(t.relative_to(box))}
        if pytest_ok:
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q", str(t)],
                    cwd=str(box), capture_output=True, text=True,
                    timeout=timeout)
                entry["returncode"] = r.returncode
                entry["tail"] = (r.stdout or r.stderr or "")[-400:]
                if r.returncode == 0:
                    passed += 1
                else:
                    failed += 1
            except subprocess.TimeoutExpired:
                entry["returncode"] = -1
                entry["tail"] = "TIMEOUT"
                failed += 1
            except Exception as e:
                entry["returncode"] = -1
                entry["tail"] = f"{type(e).__name__}: {e}"
                failed += 1
        else:
            try:
                r = subprocess.run(
                    [sys.executable, str(t)],
                    cwd=str(box), capture_output=True, text=True,
                    timeout=timeout)
                entry["returncode"] = r.returncode
                entry["tail"] = (r.stdout or r.stderr or "")[-400:]
                if r.returncode == 0:
                    passed += 1
                else:
                    failed += 1
            except subprocess.TimeoutExpired:
                entry["returncode"] = -1
                entry["tail"] = "TIMEOUT"
                failed += 1
            except Exception as e:
                entry["returncode"] = -1
                entry["tail"] = f"{type(e).__name__}: {e}"
                failed += 1
        results.append(entry)

    return {"ran": len(tests), "passed": passed, "failed": failed,
            "details": results}


def run_tests(proposal_id):
    """Full test pipeline. Returns a structured result dict."""
    start = time.time()
    box = prepare(proposal_id)

    imports = _isolated_import_test(box)
    tests = _run_test_files(box)

    result = {
        "proposal_id": int(proposal_id),
        "sandbox_path": str(box),
        "elapsed_sec": round(time.time() - start, 2),
        "imports": imports,
        "tests": tests,
        "pass": (not imports["broken"]) and tests["failed"] == 0,
    }

    audit.log("sandbox_tested", actor="lab",
              payload={
                  "pid": int(proposal_id),
                  "pass": result["pass"],
                  "import_broken": len(imports["broken"]),
                  "tests_ran": tests["ran"],
                  "tests_failed": tests["failed"],
              })
    return result


def cleanup(proposal_id):
    box = SANDBOX_ROOT / f"prop_{int(proposal_id)}"
    if box.exists():
        shutil.rmtree(box, ignore_errors=True)
        return True
    return False


def cleanup_all():
    if not SANDBOX_ROOT.exists():
        return 0
    n = 0
    for d in SANDBOX_ROOT.iterdir():
        if d.is_dir() and d.name.startswith("prop_"):
            shutil.rmtree(d, ignore_errors=True)
            n += 1
    return n


def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if not cmd:
        print("usage: python -m mimi.upgrade.sandbox "
              "<test <pid> | clean <pid> | clean-all>")
        return
    if cmd == "test" and len(sys.argv) > 2:
        r = run_tests(sys.argv[2])
        print(f"  pass         : {r['pass']}")
        print(f"  elapsed      : {r['elapsed_sec']}s")
        print(f"  imports ok   : {r['imports']['ok']}")
        print(f"  imports fail : {len(r['imports']['broken'])}")
        for b in r["imports"]["broken"][:5]:
            print(f"    X {b['module']}: {b['error'][:60]}")
        print(f"  tests ran    : {r['tests']['ran']}")
        print(f"  tests passed : {r['tests']['passed']}")
        print(f"  tests failed : {r['tests']['failed']}")
        print(f"  sandbox path : {r['sandbox_path']}")
    elif cmd == "clean" and len(sys.argv) > 2:
        ok = cleanup(sys.argv[2])
        print(f"  cleaned: {ok}")
    elif cmd == "clean-all":
        n = cleanup_all()
        print(f"  cleaned {n} sandbox(es)")
    else:
        print("unknown command")


if __name__ == "__main__":
    main()
