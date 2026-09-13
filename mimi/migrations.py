"""Agent Mimi - schema migrations."""
from datetime import datetime
from .database import db

SCHEMA_VERSION = 1


def create_version_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_version (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        version INTEGER NOT NULL,
        updated_at TEXT NOT NULL)""")


def get_version(conn):
    r = conn.execute("SELECT version FROM schema_version WHERE id=1").fetchone()
    return r[0] if r else 0


def set_version(conn, v):
    conn.execute("""INSERT INTO schema_version (id, version, updated_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET version=excluded.version,
        updated_at=excluded.updated_at""",
        (v, datetime.now().isoformat(timespec="seconds")))


def create_foundation_tables(conn):
    tables = {
        "goals": "(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, deadline TEXT, priority TEXT DEFAULT 'medium', progress INTEGER DEFAULT 0, status TEXT DEFAULT 'active', created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "missions": "(id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER, title TEXT NOT NULL, description TEXT, deadline TEXT, priority TEXT DEFAULT 'medium', progress INTEGER DEFAULT 0, status TEXT DEFAULT 'active', created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "tasks": "(id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id INTEGER, title TEXT NOT NULL, description TEXT, due_date TEXT, priority TEXT DEFAULT 'medium', status TEXT DEFAULT 'pending', completed_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "study_sessions": "(id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, study_date TEXT NOT NULL, duration_minutes INTEGER DEFAULT 0, questions_solved INTEGER DEFAULT 0, correct_answers INTEGER DEFAULT 0, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "finance": "(id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_date TEXT NOT NULL, transaction_type TEXT NOT NULL, category TEXT, amount REAL NOT NULL, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "debts": "(id INTEGER PRIMARY KEY AUTOINCREMENT, person TEXT NOT NULL, debt_type TEXT NOT NULL, original_amount REAL NOT NULL, paid_amount REAL DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_date TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "daily_logs": "(id INTEGER PRIMARY KEY AUTOINCREMENT, log_date TEXT UNIQUE NOT NULL, wake_time TEXT, sleep_time TEXT, study_hours REAL DEFAULT 0, productive_hours REAL DEFAULT 0, wasted_hours REAL DEFAULT 0, exercise_minutes INTEGER DEFAULT 0, phone_usage_minutes INTEGER DEFAULT 0, income REAL DEFAULT 0, expense REAL DEFAULT 0, energy INTEGER DEFAULT 5, important_event TEXT, journal TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "journal": "(id INTEGER PRIMARY KEY AUTOINCREMENT, entry_date TEXT NOT NULL, title TEXT, content TEXT NOT NULL, mood TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "time_logs": "(id INTEGER PRIMARY KEY AUTOINCREMENT, log_date TEXT NOT NULL, category TEXT NOT NULL, start_time TEXT, end_time TEXT, duration_minutes INTEGER DEFAULT 0, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "sleep": "(id INTEGER PRIMARY KEY AUTOINCREMENT, sleep_date TEXT NOT NULL, sleep_time TEXT, wake_time TEXT, duration_minutes INTEGER DEFAULT 0, quality INTEGER DEFAULT 0, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "routines": "(id INTEGER PRIMARY KEY AUTOINCREMENT, routine_date TEXT NOT NULL, habit TEXT NOT NULL, completed INTEGER DEFAULT 0, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        
        "faith": "(id INTEGER PRIMARY KEY AUTOINCREMENT, faith_date TEXT NOT NULL, activity TEXT NOT NULL, completed INTEGER DEFAULT 0, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "learning": "(id INTEGER PRIMARY KEY AUTOINCREMENT, learning_date TEXT NOT NULL, topic TEXT NOT NULL, source TEXT, duration_minutes INTEGER DEFAULT 0, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "career": "(id INTEGER PRIMARY KEY AUTOINCREMENT, organization TEXT NOT NULL, position TEXT NOT NULL, application_date TEXT, exam_date TEXT, status TEXT DEFAULT 'applied', preparation_progress INTEGER DEFAULT 0, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "productivity": "(id INTEGER PRIMARY KEY AUTOINCREMENT, log_date TEXT NOT NULL, productive_minutes INTEGER DEFAULT 0, wasted_minutes INTEGER DEFAULT 0, score INTEGER DEFAULT 0, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
    }
    for name, body in tables.items():
        conn.execute(f"CREATE TABLE IF NOT EXISTS {name} {body}")

    conn.execute("""CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY, value TEXT, description TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS intelligence_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
        severity TEXT DEFAULT 'info', title TEXT, message TEXT, module TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL,
        priority TEXT DEFAULT 'normal', title TEXT NOT NULL,
        message TEXT NOT NULL, source_module TEXT,
        is_read INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, log_type TEXT NOT NULL,
        message TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS backup_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, backup_type TEXT NOT NULL,
        file_path TEXT, status TEXT DEFAULT 'success',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS export_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, export_type TEXT NOT NULL,
        file_path TEXT, status TEXT DEFAULT 'success',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


def run():
    with db() as conn:
        create_version_table(conn)
        if get_version(conn) < SCHEMA_VERSION:
            create_foundation_tables(conn)
            set_version(conn, SCHEMA_VERSION)
