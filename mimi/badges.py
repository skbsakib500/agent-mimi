"""Badges / achievements tracker."""
from .database import db, fetch_one, fetch_all

# (code, icon, label, description)
BADGES = [
    ("first_task",   "🎯", "First Task",       "Complete your first task"),
    ("ten_tasks",    "✅", "Task Master",      "Complete 10 tasks"),
    ("first_goal",   "🏆", "First Goal",       "Create your first goal"),
    ("goal_100",     "👑", "Goal Crusher",     "Reach 100% on a goal"),
    ("study_10h",    "📚", "Scholar",          "Log 10 hours of study"),
    ("study_100h",   "🎓", "Grandmaster",      "Log 100 hours of study"),
    ("streak_7",     "🔥", "On Fire",          "7-day study streak"),
    ("streak_30",    "⚡", "Unstoppable",      "30-day study streak"),
    ("journal_10",   "📔", "Reflective",       "Write 10 journal entries"),
    ("pomodoro_10",  "🍅", "Focused",          "Complete 10 pomodoros"),
    ("finance_50",   "💰", "Accountant",       "Log 50 finance records"),
    ("no_overdue",   "🧘", "Zen",              "Zero overdue tasks"),
    ("level_5",      "⭐", "Rising Star",      "Reach level 5"),
    ("level_10",     "🌟", "Commander",        "Reach level 10"),
    ("level_20",     "💫", "Nova",             "Reach level 20"),
    ("all_modules",  "🧠", "Explorer",         "Try every module once"),
    ("early_bird",   "🌅", "Early Bird",       "Log study before 6 AM"),
    ("night_owl",    "🦉", "Night Owl",        "Log study after 10 PM"),
    ("perfectionist", "💎", "Perfectionist",   "100% correct answers on 5 sessions"),
    ("phoenix",      "🕊️", "Phoenix",         "Return after 7 days offline"),
]


def _ensure_table():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                code TEXT PRIMARY KEY,
                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


def unlocked():
    _ensure_table()
    rows = fetch_all("SELECT code, unlocked_at FROM user_badges")
    return {r["code"]: r["unlocked_at"] for r in rows}


def unlock(code):
    _ensure_table()
    if code not in {b[0] for b in BADGES}:
        return False
    with db() as conn:
        cur = conn.execute("SELECT code FROM user_badges WHERE code=?", (code,)).fetchone()
        if cur:
            return False
        conn.execute("INSERT INTO user_badges (code) VALUES (?)", (code,))
    return True


def info(code):
    for c, icon, label, desc in BADGES:
        if c == code:
            return {"code": c, "icon": icon, "label": label, "desc": desc}
    return None


def check_all():
    """Run all auto-checks. Returns list of newly-unlocked badge codes."""
    _ensure_table()
    from .database import fetch_one as q
    from .xp import level_info
    new = []

    def _c(sql, params=()):
        try:
            r = q(sql, params)
            return r[0] if r else 0
        except Exception:
            return 0

    tasks_done = _c("SELECT COUNT(*) FROM tasks WHERE status='completed'")
    if tasks_done >= 1 and unlock("first_task"): new.append("first_task")
    if tasks_done >= 10 and unlock("ten_tasks"): new.append("ten_tasks")

    goals = _c("SELECT COUNT(*) FROM goals")
    if goals >= 1 and unlock("first_goal"): new.append("first_goal")
    if _c("SELECT COUNT(*) FROM goals WHERE progress=100") >= 1 and unlock("goal_100"):
        new.append("goal_100")

    study_min = _c("SELECT COALESCE(SUM(duration_minutes),0) FROM study_sessions")
    study_h = study_min / 60.0
    if study_h >= 10 and unlock("study_10h"): new.append("study_10h")
    if study_h >= 100 and unlock("study_100h"): new.append("study_100h")

    journ = _c("SELECT COUNT(*) FROM journal")
    if journ >= 10 and unlock("journal_10"): new.append("journal_10")

    pomo = _c("SELECT COUNT(*) FROM study_sessions WHERE notes='pomodoro'")
    if pomo >= 10 and unlock("pomodoro_10"): new.append("pomodoro_10")

    fin = _c("SELECT COUNT(*) FROM finance")
    if fin >= 50 and unlock("finance_50"): new.append("finance_50")

    overdue = _c("""SELECT COUNT(*) FROM tasks
                    WHERE status IN ('pending','in_progress')
                    AND due_date IS NOT NULL AND due_date < date('now')""")
    total_t = _c("SELECT COUNT(*) FROM tasks")
    if total_t > 0 and overdue == 0 and unlock("no_overdue"):
        new.append("no_overdue")

    lvl = level_info()["level"]
    if lvl >= 5 and unlock("level_5"): new.append("level_5")
    if lvl >= 10 and unlock("level_10"): new.append("level_10")
    if lvl >= 20 and unlock("level_20"): new.append("level_20")

    perfect = _c("""SELECT COUNT(*) FROM study_sessions
                    WHERE questions_solved > 0
                    AND questions_solved = correct_answers""")
    if perfect >= 5 and unlock("perfectionist"): new.append("perfectionist")

    return new


def main():
    from .ui import GREEN, RED, YELLOW, c, clear, header, pause, section
    clear()
    header("BADGES", "Achievements")
    got = unlocked()
    total = len(BADGES)
    have = len(got)
    print(f"\n  Progress: {have}/{total}\n")
    for code, icon, label, desc in BADGES:
        if code in got:
            print(f"  {icon} " + c(label, GREEN) + f" — {desc}")
        else:
            print(f"  🔒 {label} — {desc}")
    pause()


run = main
