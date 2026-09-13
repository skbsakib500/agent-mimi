"""Intelligence - insights and risk detection."""
from .core import VERSION
from .database import db
from .ui import (GREEN, RED, YELLOW, c, clear, header, pause, section)

def main():
    clear(); header("INTELLIGENCE", f"v{VERSION} | Insights")
    with db() as conn:
        goals = conn.execute("""SELECT id, title, progress FROM goals
                                WHERE status='active' AND progress=0""").fetchall()
        missions = conn.execute("""SELECT id, title, progress FROM missions
                                   WHERE status='active' AND progress=0""").fetchall()
        overdue = conn.execute("""SELECT COUNT(*) AS n FROM tasks
                                  WHERE status IN ('pending','in_progress')
                                  AND due_date < date('now')""").fetchone()["n"]
        study = conn.execute("""SELECT COALESCE(SUM(duration_minutes),0)/60.0 AS h
                                FROM study_sessions
                                WHERE study_date>=date('now','-6 days')""").fetchone()["h"]
        fin = conn.execute("""SELECT
            COALESCE(SUM(CASE WHEN transaction_type='income'  THEN amount ELSE 0 END),0) AS inc,
            COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) AS exp
            FROM finance""").fetchone()
        bal = float(fin["inc"]) - float(fin["exp"])

    risks = []
    if goals:
        risks.append(f"{len(goals)} active goal(s) at 0% progress.")
    if missions:
        risks.append(f"{len(missions)} active mission(s) at 0% progress.")
    if overdue:
        risks.append(f"{overdue} overdue task(s).")
    if study < 7:
        risks.append(f"Study hours below 7h/week ({study:.1f}h).")
    if bal < 0:
        risks.append(f"Cash flow negative ({bal:,.2f}).")

    section("RISKS", "[!]")
    if risks:
        for r in risks:
            print(c(f"  ! {r}", YELLOW))
    else:
        print(c("  OK No major risks.", GREEN))

    section("RECOMMENDATIONS", "[*]")
    recs = []
    if goals:
        recs.append("Break the 0% goal into 3 smaller missions this week.")
    if overdue:
        recs.append("Clear overdue tasks first - they block momentum.")
    if study < 7:
        recs.append("Schedule two 2-hour study blocks to close the gap.")
    if bal < 0:
        recs.append("Record all expenses; review subscriptions.")
    if not recs:
        recs.append("Maintain rhythm. Consistency compounds.")
    for r in recs:
        print(f"  - {r}")
    pause()

run = main
