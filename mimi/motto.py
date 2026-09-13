"""Personal motto stored in system_config."""
from .database import fetch_one, execute

DEFAULT = "Discipline beats motivation."


def get():
    try:
        r = fetch_one("SELECT value FROM system_config WHERE key='motto'")
        return (r["value"] if r and r["value"] else DEFAULT)
    except Exception:
        return DEFAULT


def set_text(text):
    execute("""INSERT INTO system_config (key, value, description)
               VALUES ('motto', ?, 'Personal motto on dashboard')
               ON CONFLICT(key) DO UPDATE SET
               value=excluded.value,
               updated_at=CURRENT_TIMESTAMP""", (text,))
    return text
