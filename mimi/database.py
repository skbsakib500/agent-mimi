"""Agent Mimi - database layer."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "mimi.db"


def _ensure():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def connect():
    _ensure()
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    return c


@contextmanager
def db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        try: conn.rollback()
        except Exception: pass
        raise
    finally:
        conn.close()


def execute(q, p=()):
    with db() as c: return c.execute(q, p)


def fetch_one(q, p=()):
    with db() as c: return c.execute(q, p).fetchone()


def fetch_all(q, p=()):
    with db() as c: return c.execute(q, p).fetchall()


def table_exists(name):
    return fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                     (name,)) is not None


def get_tables():
    return [r["name"] for r in fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]


def ensure_schema():
    from .migrations import (create_version_table, create_foundation_tables,
                             get_version, set_version, SCHEMA_VERSION as T)
    with db() as conn:
        create_version_table(conn)
        if get_version(conn) < T:
            create_foundation_tables(conn)
            set_version(conn, T)
