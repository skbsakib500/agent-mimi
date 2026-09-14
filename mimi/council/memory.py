"""Council - department memory.

Each department has its own persistent memory: past decisions,
learnings, observations. Stored in a single table keyed by dept.
"""
from datetime import datetime
from ..database import execute, fetch_one, fetch_all
from ..guardian import audit


def ensure_table():
    execute("""CREATE TABLE IF NOT EXISTS dept_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept TEXT NOT NULL,
        kind TEXT NOT NULL,
        key TEXT,
        value TEXT,
        importance INTEGER DEFAULT 5,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


def remember(dept, kind, value, key=None, importance=5):
    ensure_table()
    execute("""INSERT INTO dept_memory
               (dept, kind, key, value, importance)
               VALUES (?, ?, ?, ?, ?)""",
            (dept, kind, key, str(value)[:2000], int(importance)))
    audit.log(f"memory_write:{dept}", actor=dept,
              payload={"kind": kind, "importance": importance})


def recall(dept, kind=None, limit=20):
    ensure_table()
    if kind:
        rows = fetch_all(
            """SELECT * FROM dept_memory WHERE dept=? AND kind=?
               ORDER BY importance DESC, id DESC LIMIT ?""",
            (dept, kind, limit))
    else:
        rows = fetch_all(
            """SELECT * FROM dept_memory WHERE dept=?
               ORDER BY importance DESC, id DESC LIMIT ?""",
            (dept, limit))
    return [dict(r) for r in rows]


def search(query, limit=20):
    ensure_table()
    q = f"%{query}%"
    rows = fetch_all(
        """SELECT * FROM dept_memory
           WHERE value LIKE ? OR key LIKE ?
           ORDER BY importance DESC, id DESC LIMIT ?""",
        (q, q, limit))
    return [dict(r) for r in rows]


def forget(dept, memory_id):
    ensure_table()
    execute("DELETE FROM dept_memory WHERE dept=? AND id=?",
            (dept, int(memory_id)))


def stats():
    ensure_table()
    rows = fetch_all(
        """SELECT dept, COUNT(*) AS n FROM dept_memory
           GROUP BY dept ORDER BY n DESC""")
    return [dict(r) for r in rows]
