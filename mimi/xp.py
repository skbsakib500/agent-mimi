"""XP and level system."""
from .database import db, fetch_one

# XP awards
XP = {
    "task_complete":   25,
    "mission_done":   100,
    "goal_done":      200,
    "study_hour":      15,
    "pomodoro":        30,
    "journal":         10,
    "daily_log":       15,
    "routine_done":     5,
    "finance_entry":    5,
    "motto_edit":       2,
}

# Level thresholds: (level, cumulative_xp_required)
LEVELS = [
    (1, 0), (2, 100), (3, 250), (4, 500), (5, 900),
    (6, 1500), (7, 2400), (8, 3700), (9, 5500), (10, 8000),
    (11, 11500), (12, 16000), (13, 22000), (14, 30000),
    (15, 40000), (16, 55000), (17, 75000), (18, 100000),
    (19, 150000), (20, 250000),
]

TITLES = {
    1: "Initiate", 2: "Apprentice", 3: "Tracker", 4: "Achiever",
    5: "Disciplined", 6: "Focused", 7: "Relentless", 8: "Sharp",
    9: "Consistent", 10: "Commander", 11: "Strategist",
    12: "Architect", 13: "Master", 14: "Sensei", 15: "Legend",
    16: "Mythic", 17: "Transcendent", 18: "Ascendant",
    19: "Immortal", 20: "Nova",
}


def _ensure_table():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        row = conn.execute("SELECT id FROM user_progress WHERE id=1").fetchone()
        if not row:
            conn.execute("INSERT INTO user_progress (id, xp, level) VALUES (1, 0, 1)")


def get_xp():
    _ensure_table()
    r = fetch_one("SELECT xp FROM user_progress WHERE id=1")
    return int(r["xp"] or 0) if r else 0


def level_for(xp):
    lvl = 1
    for l, req in LEVELS:
        if xp >= req:
            lvl = l
        else:
            break
    return lvl


def level_info():
    xp = get_xp()
    lvl = level_for(xp)
    # Next level threshold
    next_req = None
    for l, req in LEVELS:
        if l == lvl + 1:
            next_req = req
            break
    cur_req = dict(LEVELS).get(lvl, 0)
    if next_req is None:
        pct = 100.0
        to_next = 0
    else:
        span = next_req - cur_req
        pct = ((xp - cur_req) / span * 100.0) if span else 100.0
        to_next = next_req - xp
    return {
        "xp": xp,
        "level": lvl,
        "title": TITLES.get(lvl, "Nova"),
        "pct": max(0.0, min(100.0, pct)),
        "next_at": next_req,
        "to_next": to_next,
    }


def award(action, amount=None):
    """Award XP for an action. Returns (gained, leveled_up)."""
    _ensure_table()
    gained = amount if amount is not None else XP.get(action, 0)
    if gained <= 0:
        return 0, False

    old_level = level_info()["level"]
    with db() as conn:
        conn.execute("""UPDATE user_progress
                        SET xp = xp + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id=1""", (gained,))
    new_level = level_info()["level"]
    return gained, new_level > old_level


def reset():
    _ensure_table()
    with db() as conn:
        conn.execute("UPDATE user_progress SET xp=0, level=1 WHERE id=1")
