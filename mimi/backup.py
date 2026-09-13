"""Agent Mimi - backup manager."""
from datetime import datetime
from pathlib import Path
import sqlite3
from .database import DB_PATH, db
from .ui import GREEN, RED, c, clear, header, menu, pause

def _dir():
    d = Path(DB_PATH).parent.parent / "backups" / "manual"
    d.mkdir(parents=True, exist_ok=True)
    return d

def create_backup():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = _dir() / f"mimi_backup_{stamp}.db"
    src = sqlite3.connect(DB_PATH)
    try:
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    chk = sqlite3.connect(target)
    try:
        ok = chk.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        chk.close()
    if ok != "ok":
        target.unlink(missing_ok=True)
        raise RuntimeError("Backup failed integrity check.")
    with db() as conn:
        conn.execute("""INSERT INTO backup_logs (backup_type, file_path, status)
                        VALUES ('manual', ?, 'success')""", (str(target),))
    return target

def list_backups():
    d = _dir()
    files = sorted(d.glob("*.db"), reverse=True)
    if not files:
        print(c("\n  No backups yet.", RED))
        return
    print(c(f"\n  {len(files)} backup(s) in {d}:", GREEN))
    for f in files[:20]:
        size = f.stat().st_size / 1024
        print(f"  - {f.name}  ({size:.1f} KB)")

def main():
    while True:
        clear()
        header("BACKUP CENTER", "Safe DB snapshots")
        print("  1. Create backup now")
        print("  2. List backups")
        print("  0. Back")
        ch = input(c("\n  > Select: ")).strip()
        if ch == "1":
            try:
                p = create_backup()
                print(c(f"\n  OK Saved: {p}", GREEN))
            except Exception as e:
                print(c(f"\n  X {type(e).__name__}: {e}", RED))
            pause()
        elif ch == "2":
            list_backups(); pause()
        elif ch == "0":
            break
        else:
            print(c("  X Invalid.", RED)); pause()

run = main
