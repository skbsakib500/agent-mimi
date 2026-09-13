"""Safe single-record data management."""
from datetime import datetime
from pathlib import Path
import sqlite3
from .database import DB_PATH, db, fetch_all
from .ui import (BOLD, CYAN, GREEN, RED, YELLOW, c, header, pause)

MANAGEABLE = {
    "goals":"Goals", "missions":"Missions", "tasks":"Tasks",
    "study_sessions":"Study Sessions", "finance":"Finance",
    "debts":"Debts", "daily_logs":"Daily Logs", "journal":"Journal",
    "time_logs":"Time Logs", "sleep":"Sleep", "routines":"Routines",
    "productivity":"Productivity",
}

def _backup():
    db_path = Path(DB_PATH)
    bdir = db_path.parent.parent / "backups" / "pre_delete"
    bdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = bdir / f"mimi_pre_delete_{stamp}.db"
    src = sqlite3.connect(db_path)
    try:
        dst = sqlite3.connect(target)
        try: src.backup(dst)
        finally: dst.close()
    finally: src.close()
    chk = sqlite3.connect(target)
    try:
        ok = chk.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        chk.close()
    if ok != "ok":
        target.unlink(missing_ok=True)
        raise RuntimeError("Backup failed integrity check.")
    return target

def _choose():
    items = list(MANAGEABLE.items())
    print(c("\n  SELECT TABLE", BOLD+CYAN))
    for i, (_, l) in enumerate(items, 1):
        print(f"  {i:>2}. {l}")
    print("   0. Back")
    raw = input(c("\n  > Table: ", BOLD)).strip()
    if raw == "0": return None
    try:
        idx = int(raw)-1
        if 0 <= idx < len(items): return items[idx][0]
    except ValueError:
        pass
    print(c("  X Invalid.", RED))
    pause()
    return None

def list_records(table):
    rows = fetch_all(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 50")
    if not rows:
        print(c("\n  None.", YELLOW)); return
    print(c(f"\n  {MANAGEABLE[table]} - latest 50", BOLD+CYAN))
    for r in rows:
        print("  " + " | ".join(f"{k}={r[k]}" for k in r.keys()))

def delete_record(table, rid):
    with db() as conn:
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
        if not row:
            print(c("  X Not found.", RED)); return
        print(c("\n  DESTRUCTIVE", BOLD+RED))
        print(f"  Table: {MANAGEABLE[table]}   ID: {rid}")
        if input(c("\n  Type DELETE: ", BOLD+YELLOW)).strip() != "DELETE":
            print(c("  Cancelled.", GREEN)); return
        bkp = _backup()
        conn.execute(f"DELETE FROM {table} WHERE id=?", (rid,))
        conn.execute("""INSERT INTO system_logs (log_type, message)
                        VALUES (?, ?)""",
                     ("data_management", f"DELETE: {table}, id={rid}"))
    print(c(f"\n  Deleted. Backup: {bkp}", GREEN))

def main():
    while True:
        header("DATA MANAGEMENT", "Safe destructive ops with auto backup")
        print("\n  1. List records   2. Delete record   0. Back")
        ch = input(c("\n  > Select: ", BOLD)).strip()
        if ch == "0": return
        if ch == "1":
            t = _choose()
            if t:
                list_records(t); pause()
            continue
        if ch == "2":
            t = _choose()
            if t:
                try:
                    rid = int(input(c("  ID: ", BOLD)).strip())
                    delete_record(t, rid)
                except ValueError:
                    print(c("  X Invalid ID.", RED))
                except Exception as e:
                    print(c(f"  X {type(e).__name__}: {e}", RED))
                pause()
            continue
        print(c("  X Invalid.", RED)); pause()
