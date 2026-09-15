"""Central API key + endpoint manager."""
import os
from .database import fetch_one, execute

KEYS = {
    "gemini":     "GEMINI_API_KEY",
    "openai":     "OPENAI_API_KEY",
    "anthropic":  "ANTHROPIC_API_KEY",
    "deepseek":   "DEEPSEEK_API_KEY",
    "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
    "telegram_chat_id":   "TELEGRAM_CHAT_ID",
    "groq":       "GROQ_API_KEY",
    "mistral":    "MISTRAL_API_KEY",
    "openweather":"OPENWEATHER_API_KEY",
    "google_maps":"GOOGLE_MAPS_API_KEY",
    "google_client_id": "GOOGLE_CLIENT_ID",
    "google_client_secret": "GOOGLE_CLIENT_SECRET",
    "google_cal": "GOOGLE_CALENDAR_ID",
}


def _ensure():
    with __import__("mimi.database", fromlist=["db"]).db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                name TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


def get(name):
    """DB first, then env."""
    _ensure()
    r = fetch_one("SELECT value FROM api_keys WHERE name=?", (name,))
    if r and r["value"]:
        return r["value"]
    env = KEYS.get(name)
    return os.environ.get(env, "") if env else ""


def set_key(name, value):
    _ensure()
    execute("""INSERT INTO api_keys (name, value)
               VALUES (?, ?)
               ON CONFLICT(name) DO UPDATE SET
               value=excluded.value,
               updated_at=CURRENT_TIMESTAMP""", (name, value.strip()))
    return True


def unset_key(name):
    _ensure()
    execute("DELETE FROM api_keys WHERE name=?", (name,))


def list_keys():
    _ensure()
    rows = fetch_one("SELECT COUNT(*) AS n FROM api_keys")
    stored = {}
    from .database import fetch_all
    for r in fetch_all("SELECT name, value FROM api_keys"):
        stored[r["name"]] = bool(r["value"])
    out = {}
    for name in KEYS:
        env = KEYS[name]
        val = stored.get(name) or bool(os.environ.get(env))
        out[name] = "set" if val else "missing"
    return out


def status_str():
    s = list_keys()
    parts = []
    for k, v in s.items():
        parts.append(f"{k}={'OK' if v=='set' else 'X'}")
    return "  ".join(parts)


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    while True:
        clear()
        header("🔑 API KEYS", "Central key manager")
        s = list_keys()
        print()
        for name, status in s.items():
            icon = c("OK", GREEN) if status == "set" else c("--", RED)
            print(f"  [{icon}] {name:<14} (env: {KEYS[name]})")
        print()
        print("  1. Set key   2. Remove key   0. Back")
        ch = input(c("\n  > Select: ")).strip()
        if ch == "0":
            break
        if ch == "1":
            name = input("  Key name: ").strip().lower()
            if name not in KEYS:
                print(c("  X Unknown key name.", RED)); pause(); continue
            val = input(f"  Value for {name}: ").strip()
            if val:
                set_key(name, val)
                print(c("  OK Saved.", GREEN))
            pause()
        elif ch == "2":
            name = input("  Key name: ").strip().lower()
            unset_key(name)
            print(c("  Removed.", GREEN))
            pause()

run = main
