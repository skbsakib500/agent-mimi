"""Git-backed cloud sync for Mimi."""
import subprocess, os
from pathlib import Path
from datetime import datetime
from .database import BASE_DIR

def _run(args, cwd=None):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd or BASE_DIR,
                           capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return -1, "", "git not installed"
    except Exception as e:
        return -1, "", f"{type(e).__name__}: {e}"

def git_available():
    code, _, _ = _run(["--version"])
    return code == 0

def is_repo():
    return (BASE_DIR / ".git").exists()

def init_repo():
    if is_repo():
        return True, "already initialized"
    code, _, err = _run(["init"])
    if code != 0:
        return False, err
    _run(["branch", "-M", "main"])
    with (BASE_DIR / ".gitignore").open("w") as f:
        f.write("""__pycache__/
*.pyc
data/*.db-shm
data/*.db-wal
data/profiles/*/mimi.db-shm
data/profiles/*/mimi.db-wal
.termux/
exports/
reports/
backups/
""")
    return True, "initialized"

def status():
    if not is_repo():
        return None
    code, out, err = _run(["status", "--porcelain"])
    if code != 0:
        return None
    return out.splitlines() if out else []

def add_remote(url):
    code, out, err = _run(["remote"])
    if "origin" in out:
        _run(["remote", "set-url", "origin", url])
    else:
        _run(["remote", "add", "origin", url])
    return True

def remote_url():
    code, out, _ = _run(["remote", "get-url", "origin"])
    return out if code == 0 else ""

def commit(msg=None):
    if not is_repo():
        return False, "not a git repo"
    _run(["add", "-A"])
    if not msg:
        msg = f"Mimi sync {datetime.now():%Y-%m-%d %H:%M}"
    code, out, err = _run(["commit", "-m", msg])
    if code != 0 and "nothing to commit" not in (out + err).lower():
        return False, err or out
    return True, "committed"

def push():
    if not is_repo():
        return False, "not a repo"
    commit()
    code, out, err = _run(["push", "-u", "origin", "main"])
    if code != 0:
        return False, err or out
    return True, "pushed"

def pull():
    if not is_repo():
        return False, "not a repo"
    code, out, err = _run(["pull", "origin", "main", "--no-rebase"])
    if code != 0:
        return False, err or out
    return True, out or "pulled"

def full_status():
    return {
        "git":       git_available(),
        "repo":      is_repo(),
        "remote":    remote_url(),
        "changes":   len(status() or []),
    }

def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    while True:
        clear()
        header("☁️  CLOUD SYNC", "Git-backed")
        s = full_status()
        section("STATUS", "📊")
        print(f"  git binary  : {'OK' if s['git'] else 'MISSING'}")
        print(f"  repo        : {'OK' if s['repo'] else 'not initialized'}")
        print(f"  remote      : {s['remote'] or '(none)'}")
        print(f"  changes     : {s['changes']}")
        print()
        print("  1. Initialize repo")
        print("  2. Set remote URL (GitHub)")
        print("  3. Push now")
        print("  4. Pull now")
        print("  5. Show changes")
        print("  0. Back")
        ch = input(c("\n  > Select: ")).strip()
        if ch == "0":
            break
        elif ch == "1":
            ok, msg = init_repo()
            print(c(f"  {'OK ' + msg if ok else 'X ' + msg}", GREEN if ok else RED))
            pause()
        elif ch == "2":
            url = input("  Remote URL: ").strip()
            if url:
                add_remote(url)
                print(c("  OK Saved.", GREEN))
            pause()
        elif ch == "3":
            ok, msg = push()
            print(c(f"  {'OK ' + msg if ok else 'X ' + msg}", GREEN if ok else RED))
            pause()
        elif ch == "4":
            ok, msg = pull()
            print(c(f"  {'OK ' + msg if ok else 'X ' + msg}", GREEN if ok else RED))
            pause()
        elif ch == "5":
            ch_lines = status() or []
            if not ch_lines:
                print(c("\n  No changes.", GREEN))
            for line in ch_lines[:30]:
                print(f"  {line}")
            pause()

run = main
