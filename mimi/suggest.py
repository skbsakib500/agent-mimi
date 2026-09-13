"""Smart suggestions from patterns."""
from datetime import datetime, date, timedelta
from .database import fetch_one, fetch_all


def _n(q, default=0):
    try:
        r = fetch_one(q)
        return r[0] if r else default
    except Exception:
        return default


def _rows(q, p=()):
    try:
        return fetch_all(q, p)
    except Exception:
        return []


def analyze():
    """Return list of {icon, title, body, priority}."""
    out = []

    # 1. Overdue tasks
    n = _n("""SELECT COUNT(*) FROM tasks
              WHERE status IN ('pending','in_progress')
              AND due_date IS NOT NULL AND due_date < date('now')""")
    if n:
        out.append({"icon": "⚠", "priority": "high",
                    "title": f"{n} overdue task(s)",
                    "body": "Clear them first - they block momentum."})

    # 2. Study streak check
    rows = _rows("""SELECT DISTINCT study_date FROM study_sessions
                    ORDER BY study_date DESC LIMIT 14""")
    dates = [r["study_date"] for r in rows]
    streak = 0
    today = date.today()
    for i, d in enumerate(dates):
        try:
            dd = datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            continue
        if dd == today - timedelta(days=i):
            streak += 1
        else:
            break
    if streak == 0:
        out.append({"icon": "📚", "priority": "high",
                    "title": "No study streak",
                    "body": "Start a 25-min pomodoro now. Small wins build habit."})
    elif streak >= 7:
        out.append({"icon": "🔥", "priority": "low",
                    "title": f"{streak}-day streak",
                    "body": "Don't break it. Even 15 min today counts."})

    # 3. Study weekly target
    h = _n("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
              FROM study_sessions WHERE study_date >= date('now','-6 days')""")
    if h < 3:
        out.append({"icon": "📖", "priority": "medium",
                    "title": f"Only {h:.1f}h study this week",
                    "body": "Target 7h. Two 2-hour blocks close the gap."})

    # 4. Sleep
    slp = _n("""SELECT COALESCE(AVG(duration_minutes),0)
                FROM sleep WHERE sleep_date >= date('now','-6 days')""")
    if slp and slp < 360:
        out.append({"icon": "😴", "priority": "medium",
                    "title": f"Sleep avg {slp/60:.1f}h",
                    "body": "Aim for 7h+. Chronic short sleep hurts focus."})

    # 5. Finance
    bal = _n("""SELECT
        COALESCE(SUM(CASE WHEN transaction_type='income'  THEN amount ELSE 0 END),0) -
        COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0)
        FROM finance""")
    if bal < 0:
        out.append({"icon": "💰", "priority": "high",
                    "title": f"Negative balance: ৳{bal:,.0f}",
                    "body": "Review this week's expenses - find one cut."})

    # 6. Goal stagnation
    stuck = _n("""SELECT COUNT(*) FROM goals
                  WHERE status='active'
                  AND (progress IS NULL OR progress=0)""")
    if stuck:
        out.append({"icon": "🎯", "priority": "medium",
                    "title": f"{stuck} goal(s) at 0%",
                    "body": "Break each into 3 concrete missions."})

    # 7. Daily log
    today_s = str(date.today())
    if not _n(f"SELECT COUNT(*) FROM daily_logs WHERE log_date='{today_s}'"):
        out.append({"icon": "📅", "priority": "low",
                    "title": "No daily log today",
                    "body": "Two minutes to log keeps the streak honest."})

    # 8. Best study hour
    hour = _rows("""SELECT substr(created_at,12,2) AS h,
                    SUM(duration_minutes) AS m
                    FROM study_sessions GROUP BY h
                    ORDER BY m DESC LIMIT 1""")
    if hour and hour[0]["h"]:
        out.append({"icon": "🕐", "priority": "low",
                    "title": f"Peak focus: {hour[0]['h']}:00",
                    "body": "Schedule your hardest task around this hour."})

    # Sort by priority
    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda x: order.get(x["priority"], 3))
    return out


def main():
    from .ui import BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW
    from .ui import c, clear, header, pause, section
    clear()
    header("💡 SMART SUGGESTIONS", "Based on your patterns")
    items = analyze()
    if not items:
        print()
        print(c("  Everything looks good, boss.", GREEN))
        pause()
        return
    print()
    for s in items:
        color = RED if s["priority"] == "high" else YELLOW if s["priority"] == "medium" else GREEN
        print(c(f"  {s['icon']} {s['title']}", BOLD + color))
        print(c(f"     {s['body']}", DIM + WHITE))
        print()
    pause()

run = main
