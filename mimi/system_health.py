"""System Health Center."""
from .database import DB_PATH, db, get_tables, table_exists
from .ui import GREEN, RED, c, clear, header, pause, section

REQUIRED = ("goals","missions","tasks","study_sessions","finance","debts",
            "daily_logs","intelligence_logs","recommendations","system_logs")

def main(categories=None):
    clear(); header("SYSTEM HEALTH", "Read-only diagnostics")
    exists = DB_PATH.exists()
    integrity = "missing"
    tables = 0
    if exists:
        try:
            with db() as conn:
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            tables = len(get_tables())
        except Exception as e:
            integrity = f"error: {type(e).__name__}"
    missing = [t for t in REQUIRED if not table_exists(t)]

    section("DATABASE", "[/]")
    print(f"  File: {DB_PATH}")
    print(f"  Exists: {'YES' if exists else 'NO'}")
    print(f"  Tables: {tables}")
    print(f"  Integrity: {integrity}")
    if missing:
        print(c("  Missing required: " + ", ".join(missing), RED))
    else:
        print(c("  Required schema: READY", GREEN))

    section("SAFETY", "[-]")
    print(c("  Read-only diagnostic. No data modified.", GREEN))
    pause()
