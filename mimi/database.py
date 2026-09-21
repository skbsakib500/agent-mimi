import sqlite3
from pathlib import Path

# DATA_DIR as pathlib.Path to support '/' operator
DATA_DIR = Path.home() / "Agent-Mimi-Classic"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "mimi.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            mission_id INTEGER DEFAULT 0,
            description TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'active'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            deadline TEXT,
            priority TEXT DEFAULT 'medium',
            progress INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.commit()
    return conn

def init_db():
    get_db().close()
