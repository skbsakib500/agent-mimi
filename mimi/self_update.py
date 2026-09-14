"""Self-upgrade system - proposes changes, waits for Sakib's approval."""
import subprocess, json
from datetime import datetime
from pathlib import Path
from .database import BASE_DIR, execute, fetch_all
from .constitution import OWNER
from .loyalty import review


def _run(args, timeout=30):
    try:
        r = subprocess.run(["git"] + args, cwd=BASE_DIR,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def ensure_proposal_table():
    execute("""CREATE TABLE IF NOT EXISTS upgrade_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proposed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        source TEXT,
        commit_sha TEXT,
        summary TEXT,
        status TEXT DEFAULT 'pending',
        decided_at TEXT,
        decided_by TEXT)""")


def fetch_remote():
    """Check Git remote for new commits."""
    ensure_proposal_table()
    code, out, err = _run(["fetch", "origin"])
    if code != 0:
        return None, err or out
    code, out, err = _run(["log", "HEAD..origin/main", "--oneline"])
    if code != 0:
        return None, err or out
    lines = [l for l in out.splitlines() if l.strip()]
    return lines, None


def propose_from_git():
    """Create proposals from new commits on origin/main."""
    lines, err = fetch_remote()
    if err:
        return [], err
    if not lines:
        return [], None
    added = []
    for line in lines:
        if not line.strip():
            continue
        sha, _, summary = line.partition(" ")
        execute("""INSERT INTO upgrade_proposals
                   (source, commit_sha, summary)
                   VALUES ('git', ?, ?)""",
                (sha, summary))
        added.append({"sha": sha, "summary": summary})
    return added, None


def list_pending():
    ensure_proposal_table()
    return fetch_all("""SELECT * FROM upgrade_proposals
                        WHERE status='pending' ORDER BY id DESC""")


def list_history(limit=20):
    ensure_proposal_table()
    return fetch_all("""SELECT * FROM upgrade_proposals
                        WHERE status!='pending'
                        ORDER BY decided_at DESC LIMIT ?""", (limit,))


def approve(proposal_id, by=OWNER):
    """Owner approves → apply. Requires constitution check."""
    allowed, reason = review("self_update_apply", {"approved_by": by})
    if not allowed:
        return False, reason

    ensure_proposal_table()
    row = None
    for r in list_pending():
        if r["id"] == int(proposal_id):
            row = r
            break
    if not row:
        return False, "proposal not found"

    # Apply: git pull
    code, out, err = _run(["pull", "origin", "main", "--no-rebase"])
    if code != 0:
        return False, err or out

    execute("""UPDATE upgrade_proposals
               SET status='applied', decided_at=CURRENT_TIMESTAMP,
                   decided_by=?
               WHERE id=?""", (by, proposal_id))
    return True, out or "applied"


def reject(proposal_id, by=OWNER, reason=""):
    ensure_proposal_table()
    execute("""UPDATE upgrade_proposals
               SET status='rejected', decided_at=CURRENT_TIMESTAMP,
                   decided_by=?
               WHERE id=?""", (by, proposal_id))
    return True, "rejected"


def self_check():
    """Mimi's self-diagnostic."""
    out = {
        "constitution_ok": False,
        "modules_ok": 0,
        "modules_total": 0,
        "git_repo": False,
        "version": None,
        "issues": [],
    }
    # Constitution
    try:
        from .constitution import is_sealed
        out["constitution_ok"] = is_sealed()
    except Exception as e:
        out["issues"].append(f"constitution: {e}")

    # Modules
    try:
        import importlib
        PKG = Path(BASE_DIR) / "mimi"
        mods = sorted(f.stem for f in PKG.glob("*.py") if f.stem != "__init__")
        out["modules_total"] = len(mods)
        for m in mods:
            try:
                importlib.import_module(f"mimi.{m}")
                out["modules_ok"] += 1
            except Exception as e:
                out["issues"].append(f"{m}: {type(e).__name__}")
    except Exception as e:
        out["issues"].append(f"modules: {e}")

    # Git
    out["git_repo"] = (Path(BASE_DIR) / ".git").exists()

    # Version
    try:
        from .core import VERSION
        out["version"] = VERSION
    except Exception:
        pass

    return out


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from .ui import c, clear, header, pause, section
    while True:
        clear()
        header("🛡 SELF-UPGRADE", f"Owner: {OWNER}")
        section("SELF-CHECK", "🩺")
        ch = self_check()
        ok_col = GREEN if ch["constitution_ok"] else RED
        print(c(f"  Constitution : {'SEALED' if ch['constitution_ok'] else 'TAMPERED'}",
                ok_col))
        mc = GREEN if ch["modules_ok"] == ch["modules_total"] else YELLOW
        print(c(f"  Modules      : {ch['modules_ok']}/{ch['modules_total']}", mc))
        print(f"  Git repo     : {'yes' if ch['git_repo'] else 'no'}")
        print(f"  Version      : {ch['version'] or '-'}")
        if ch["issues"]:
            for i in ch["issues"][:5]:
                print(c(f"  ! {i}", YELLOW))

        section("PENDING PROPOSALS", "📬")
        pending = list_pending()
        if not pending:
            print(c("  No pending upgrades.", DIM + WHITE))
        for p in pending[:5]:
            print(f"  #{p['id']} [{p['source']}] {p['summary'][:60]}")

        print()
        print("  1. Check for new commits")
        print("  2. Approve proposal (by Sakib)")
        print("  3. Reject proposal")
        print("  4. View history")
        print("  0. Back")
        sel = input(c("\n  > Select: ")).strip()

        if sel == "0":
            break
        elif sel == "1":
            added, err = propose_from_git()
            if err:
                print(c(f"  X {err}", RED))
            elif not added:
                print(c("  Up to date.", GREEN))
            else:
                print(c(f"  {len(added)} new proposal(s).", GREEN))
            pause()
        elif sel == "2":
            pid = input("  Proposal #: ").strip()
            if pid.isdigit():
                ok, msg = approve(pid)
                print(c(f"  {'OK ' + msg if ok else 'X ' + msg}",
                        GREEN if ok else RED))
            pause()
        elif sel == "3":
            pid = input("  Proposal #: ").strip()
            if pid.isdigit():
                ok, msg = reject(pid)
                print(c(f"  {msg}", GREEN))
            pause()
        elif sel == "4":
            hist = list_history(20)
            clear()
            header("UPGRADE HISTORY", "")
            for h in hist:
                print(f"  [{h['status']}] #{h['id']} {h['summary'][:50]}")
            pause()

run = main
