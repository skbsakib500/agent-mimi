"""Build rich context for the LLM from user's data."""
from datetime import date
from .database import fetch_one, fetch_all


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


def _n(sql):
    return int(_q(sql) or 0)


def _rows(sql, params=(), limit=10):
    try:
        rows = fetch_all(sql, params)
        return [dict(r) for r in rows[:limit]]
    except Exception:
        return []


def snapshot():
    lines = []
    lines.append("=== USER PROFILE ===")
    try:
        from .core import USER_NAME, VERSION
        lines.append(f"Name: {USER_NAME}")
        lines.append(f"Mimi version: {VERSION}")
    except Exception:
        pass
    try:
        from .xp import level_info
        lv = level_info()
        lines.append(f"Level: {lv['level']} ({lv['title']}), XP: {lv['xp']}")
    except Exception:
        pass

    lines.append("")
    lines.append("=== GOALS ===")
    g = _n("SELECT COUNT(*) FROM goals")
    ga = _n("SELECT COUNT(*) FROM goals WHERE status='active'")
    gp = _q("SELECT COALESCE(AVG(progress),0) FROM goals WHERE status='active'")
    lines.append(f"Total: {g}, Active: {ga}, Avg: {gp:.1f}%")
    for r in _rows("""SELECT title, progress, priority FROM goals
                      WHERE status='active' ORDER BY id DESC LIMIT 5"""):
        lines.append(f"  - {r['title']} [{r['progress']}%, {r['priority']}]")

    lines.append("")
    lines.append("=== MISSIONS ===")
    lines.append(f"Active: {_n('SELECT COUNT(*) FROM missions WHERE status=1+1')}".replace("1+1", "'active'"))
    for r in _rows("""SELECT title, progress FROM missions
                      WHERE status='active' ORDER BY id DESC LIMIT 5"""):
        lines.append(f"  - {r['title']} [{r['progress']}%]")

    lines.append("")
    lines.append("=== TASKS ===")
    tp = _n("SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')")
    tc = _n("SELECT COUNT(*) FROM tasks WHERE status='completed'")
    od = _n("""SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')
               AND due_date IS NOT NULL AND due_date < date('now')""")
    lines.append(f"Pending: {tp}, Completed: {tc}, Overdue: {od}")
    for r in _rows("""SELECT title, due_date, priority FROM tasks
                      WHERE status IN ('pending','in_progress')
                      ORDER BY COALESCE(due_date,'9999') LIMIT 8"""):
        due = r['due_date'] or '-'
        lines.append(f"  - {r['title']} [due {due}, {r['priority']}]")

    lines.append("")
    lines.append("=== STUDY (7d) ===")
    sw = _q("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
               FROM study_sessions WHERE study_date >= date('now','-6 days')""")
    st = _q("""SELECT COALESCE(SUM(duration_minutes),0)
               FROM study_sessions WHERE study_date = date('now')""")
    lines.append(f"Weekly: {sw:.1f}h, Today: {st}m")
    for r in _rows("""SELECT subject, SUM(duration_minutes) AS m
                      FROM study_sessions
                      WHERE study_date >= date('now','-6 days')
                      GROUP BY subject ORDER BY m DESC LIMIT 5"""):
        lines.append(f"  - {r['subject']}: {r['m']}m")

    lines.append("")
    lines.append("=== FINANCE ===")
    inc = _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='income'")
    exp = _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='expense'")
    lines.append(f"Income: {inc:,.0f}, Expense: {exp:,.0f}, Balance: {inc-exp:,.0f}")
    _d = _n("SELECT COUNT(*) FROM debts WHERE status='active'")
    lines.append(f"Debts: {_d}")

    lines.append("")
    lines.append("=== SLEEP (7d) ===")
    slp = _q("""SELECT COALESCE(AVG(duration_minutes),0)/60.0 FROM sleep
                WHERE sleep_date >= date('now','-6 days')""")
    lines.append(f"Avg: {slp:.1f}h")

    lines.append("")
    lines.append("=== TODAY ===")
    lines.append(f"Date: {date.today().isoformat()}")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are Mimi, a personal life agent for {user}.

You have full access to {user}'s data (shown below).
Give concise, warm, practical advice. Never moralize.
Be specific. Reference their actual numbers.
Keep replies under 150 words unless asked for detail.

{context}
"""


def build_system_prompt():
    try:
        from .core import USER_NAME
    except Exception:
        USER_NAME = "the user"
    ctx = snapshot()
    return SYSTEM_PROMPT.format(user=USER_NAME, context=ctx)
