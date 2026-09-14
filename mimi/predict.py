"""Predictive engine - forecasts and early warnings."""
from datetime import date, datetime, timedelta
from .database import fetch_one, fetch_all


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


def _rows(sql, params=(), limit=20):
    try:
        return [dict(r) for r in fetch_all(sql, params)[:limit]]
    except Exception:
        return []


def predict_goal_slips():
    """Goals with deadline coming that look unlikely to finish."""
    out = []
    today = date.today()
    for r in _rows("""SELECT id, title, progress, deadline FROM goals
                      WHERE status='active' AND deadline IS NOT NULL"""):
        try:
            d = datetime.strptime(r["deadline"], "%Y-%m-%d").date()
        except Exception:
            continue
        days = (d - today).days
        if days < 0:
            out.append({
                "title": r["title"],
                "risk": "overdue",
                "days": days,
                "progress": r["progress"],
                "msg": f"Deadline passed {abs(days)} day(s) ago at {r['progress']}%.",
            })
            continue
        if days == 0:
            continue
        rate = (r["progress"] or 0) / max(1, (30 - days))  # crude rate/day
        needed = (100 - (r["progress"] or 0)) / max(1, days)
        if needed > rate * 2.5 and r["progress"] < 90:
            out.append({
                "title": r["title"],
                "risk": "high",
                "days": days,
                "progress": r["progress"],
                "msg": f"Only {days}d left, {100-r['progress']}% to go — too fast.",
            })
    return out


def predict_task_overdue():
    """Tasks due within 3 days that are still pending — likely to slip."""
    out = _rows("""SELECT title, due_date, priority FROM tasks
                   WHERE status IN ('pending','in_progress')
                   AND due_date IS NOT NULL
                   AND due_date BETWEEN date('now') AND date('now','+3 day')
                   AND priority IN ('high','critical')
                   ORDER BY due_date""")
    return [{"title": r["title"], "due": r["due_date"], "prio": r["priority"]}
            for r in out]


def predict_study_trend():
    """Predict next 7 days study based on last 14."""
    rows = _rows("""SELECT study_date, COALESCE(SUM(duration_minutes),0) AS m
                    FROM study_sessions
                    WHERE study_date >= date('now','-13 days')
                    GROUP BY study_date ORDER BY study_date""")
    if not rows:
        return {"avg": 0.0, "trend": "flat", "predicted": 0.0, "delta": 0.0}
    vals = [float(r["m"]) for r in rows]
    n = len(vals)
    first_half = vals[:n // 2] or [0]
    second_half = vals[n // 2:] or [0]
    a = sum(first_half) / len(first_half)
    b = sum(second_half) / len(second_half)
    delta = b - a
    trend = "up" if delta > 5 else "down" if delta < -5 else "flat"
    avg = sum(vals) / len(vals)
    predicted = max(0, avg * 7 / 60.0)
    return {
        "avg": avg / 60.0,
        "trend": trend,
        "predicted": predicted,
        "delta": delta / 60.0,
    }


def predict_finance_runout():
    """Project cash based on last 14 days net flow."""
    income = _q("""SELECT COALESCE(SUM(amount),0) FROM finance
                   WHERE transaction_type='income'
                   AND transaction_date >= date('now','-13 days')""")
    expense = _q("""SELECT COALESCE(SUM(amount),0) FROM finance
                    WHERE transaction_type='expense'
                    AND transaction_date >= date('now','-13 days')""")
    net_14 = float(income) - float(expense)
    daily = net_14 / 14.0
    bal = float(_q("SELECT COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END),0) FROM finance")) - \
          float(_q("SELECT COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) FROM finance"))
    if daily >= 0:
        return {"daily": daily, "days_to_zero": None, "msg": "Cash trending up."}
    days = int(bal / abs(daily)) if bal > 0 else 0
    return {
        "daily": daily,
        "days_to_zero": days,
        "msg": f"At this rate, cash ends in {days} days." if days else "Cash flow negative.",
    }


def predict_consistency():
    """Days since last log of each type."""
    out = {}
    for label, table, col in [
        ("study", "study_sessions", "study_date"),
        ("journal", "journal", "entry_date"),
        ("daily", "daily_logs", "log_date"),
        ("sleep", "sleep", "sleep_date"),
    ]:
        r = _q(f"SELECT MAX({col}) FROM {table} WHERE {col} IS NOT NULL")
        if not r:
            out[label] = None
            continue
        try:
            d = datetime.strptime(str(r), "%Y-%m-%d").date()
            out[label] = (date.today() - d).days
        except Exception:
            out[label] = None
    return out


def forecast_all():
    return {
        "goals": predict_goal_slips(),
        "tasks": predict_task_overdue(),
        "study": predict_study_trend(),
        "finance": predict_finance_runout(),
        "consistency": predict_consistency(),
    }


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    clear()
    header("🔮 PREDICTIVE ENGINE", "Forecasts & early warnings")
    f = forecast_all()

    section("GOAL RISKS", "🎯")
    if not f["goals"]:
        print(c("  All goals on track.", GREEN))
    for g in f["goals"]:
        col = RED if g["risk"] == "overdue" else YELLOW
        print(c(f"  ⚠ {g['title']} — {g['msg']}", col))

    section("TASKS AT RISK", "📋")
    if not f["tasks"]:
        print(c("  No risky tasks.", GREEN))
    for t in f["tasks"]:
        print(c(f"  ⚠ {t['title']} (due {t['due']}, {t['prio']})", YELLOW))

    section("STUDY FORECAST", "📚")
    s = f["study"]
    arrow = "↑" if s["trend"] == "up" else "↓" if s["trend"] == "down" else "→"
    col = GREEN if s["trend"] == "up" else RED if s["trend"] == "down" else WHITE
    print(f"  Daily avg : {s['avg']:.1f}h")
    print(f"  Trend     : {c(arrow + ' ' + s['trend'], col)}")
    print(f"  Next 7d   : {s['predicted']:.1f}h (if pattern holds)")

    section("FINANCE FORECAST", "💰")
    fin = f["finance"]
    print(f"  Daily net : {fin['daily']:,.0f}")
    col = RED if fin["daily"] < 0 else GREEN
    print(c(f"  {fin['msg']}", col))

    section("HABIT FRESHNESS", "✓")
    for k, v in f["consistency"].items():
        if v is None:
            print(c(f"  {k:<10} : never logged", RED))
        elif v == 0:
            print(c(f"  {k:<10} : today ✅", GREEN))
        elif v <= 2:
            print(c(f"  {k:<10} : {v} day(s) ago", YELLOW))
        else:
            print(c(f"  {k:<10} : {v} day(s) ago (stale)", RED))

    pause()

run = main
