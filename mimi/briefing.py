"""Daily briefing."""
from datetime import datetime, date
from .database import fetch_one
from . import notify
from . import speak

def _n(q, default=0):
    try:
        r = fetch_one(q)
        return r[0] if r else default
    except Exception:
        return default

def _greet():
    h = datetime.now().hour
    if h < 12: return "Good morning"
    if h < 17: return "Good afternoon"
    return "Good evening"

def gather():
    today = str(date.today())
    return {
        "date": today,
        "greeting": _greet(),
        "goals_active": _n("SELECT COUNT(*) FROM goals WHERE status='active'"),
        "goals_avg": _n("SELECT COALESCE(AVG(progress),0) FROM goals WHERE status='active'"),
        "missions_active": _n("SELECT COUNT(*) FROM missions WHERE status='active'"),
        "tasks_overdue": _n("""SELECT COUNT(*) FROM tasks
                               WHERE status IN ('pending','in_progress')
                               AND due_date < date('now')"""),
        "tasks_today": _n("""SELECT COUNT(*) FROM tasks
                             WHERE status IN ('pending','in_progress')
                             AND due_date = date('now')"""),
        "study_week_h": _n("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
                              FROM study_sessions
                              WHERE study_date >= date('now','-6 days')"""),
        "study_today_min": _n("""SELECT COALESCE(SUM(duration_minutes),0)
                                 FROM study_sessions WHERE study_date = date('now')"""),
        "balance": _n("""SELECT
            COALESCE(SUM(CASE WHEN transaction_type='income'  THEN amount ELSE 0 END),0) -
            COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0)
            FROM finance"""),
        "daily_logged": _n(f"SELECT COUNT(*) FROM daily_logs WHERE log_date='{today}'"),
        "journal_logged": _n(f"SELECT COUNT(*) FROM journal WHERE entry_date='{today}'"),
        "sleep_avg_h": _n("""SELECT COALESCE(AVG(duration_minutes),0)/60.0
                             FROM sleep WHERE sleep_date >= date('now','-6 days')"""),
    }

def compose_text(d):
    lines = [f"{d['greeting']}, SKB Sakib.", f"Today is {d['date']}.", ""]
    if d["tasks_overdue"]:
        lines.append(f"! {d['tasks_overdue']} overdue task(s) - clear them first.")
    if d["tasks_today"]:
        lines.append(f"{d['tasks_today']} task(s) due today.")
    lines.append(f"{d['goals_active']} active goal(s), avg {d['goals_avg']:.0f}%.")
    lines.append(f"{d['missions_active']} active mission(s).")
    lines.append(f"Study this week: {d['study_week_h']:.1f}h.")
    if d["study_today_min"]:
        lines.append(f"Studied today: {d['study_today_min']} min.")
    if d["sleep_avg_h"]:
        lines.append(f"7-day sleep avg: {d['sleep_avg_h']:.1f}h.")
    if d["balance"] < 0:
        lines.append(f"Balance negative: {d['balance']:,.0f}.")
    if not d["daily_logged"]:
        lines.append("No daily log yet today.")
    if not d["journal_logged"]:
        lines.append("No journal entry yet.")
    return "\n".join(lines)

def push():
    d = gather()
    text = compose_text(d)
    notify.send("Mimi Daily Briefing", text, priority="default")
    if speak.available():
        try:
            speak.speak(text, lang="bn")
        except Exception:
            pass
    return d, text

def render():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    clear()
    header("📋 DAILY BRIEFING", "Your snapshot for today")
    d = gather()
    print()
    print(c(f"  {d['greeting']}, SKB Sakib.", BOLD + GREEN))
    print(c(f"  {d['date']}", DIM + WHITE))

    section("PRIORITIES", "🎯")
    if d["tasks_overdue"]:
        print(c(f"  ! {d['tasks_overdue']} overdue task(s)", RED))
    if d["tasks_today"]:
        print(c(f"  * {d['tasks_today']} due today", YELLOW))
    if not d["tasks_overdue"] and not d["tasks_today"]:
        print(c("  OK Nothing urgent.", GREEN))

    section("PROGRESS", "📊")
    print(f"  Goals: {d['goals_active']} active, avg {d['goals_avg']:.0f}%")
    print(f"  Missions: {d['missions_active']} active")
    print(f"  Study (7d): {d['study_week_h']:.1f}h")
    print(f"  Sleep avg: {d['sleep_avg_h']:.1f}h")
    print(f"  Balance: {d['balance']:,.0f}")

    section("HABITS", "[v]")
    print(f"  Daily log: {'YES' if d['daily_logged'] else 'NO'}")
    print(f"  Journal:   {'YES' if d['journal_logged'] else 'NO'}")

    print()
    print("  1. Push as notification   0. Back")
    ch = input(c("\n  > Select: ")).strip()
    if ch == "1":
        push()
        print(c("  Sent to notifications.", GREEN))
    pause()

run = render
