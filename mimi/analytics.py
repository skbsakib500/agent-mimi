"""Analytics - read-only performance report."""
from datetime import datetime, timedelta
from .core import VERSION
from .database import db
from .ui import (BOLD, GREEN, RED, YELLOW, c, clear, header, pause)

def _num(v, d=0):
    try: return float(v or 0)
    except (TypeError, ValueError): return d

def _range(days):
    end = datetime.now().date()
    start = end - timedelta(days=days-1)
    return start.isoformat(), end.isoformat()

def report(days=7):
    start, end = _range(days)
    with db() as conn:
        s = conn.execute("""SELECT COALESCE(SUM(duration_minutes),0) AS m,
                                   COALESCE(SUM(questions_solved),0) AS q,
                                   COALESCE(SUM(correct_answers),0) AS k,
                                   COUNT(*) AS n
                            FROM study_sessions
                            WHERE study_date BETWEEN ? AND ?""",
                         (start, end)).fetchone()
        g = conn.execute("""SELECT COUNT(*) AS t,
                            COALESCE(SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END),0) AS done,
                            COALESCE(AVG(progress),0) AS avg FROM goals""").fetchone()
        m = conn.execute("""SELECT COUNT(*) AS t,
                            COALESCE(SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END),0) AS done,
                            COALESCE(AVG(progress),0) AS avg FROM missions""").fetchone()
        f = conn.execute("""SELECT
                            COALESCE(SUM(CASE WHEN transaction_type='income'  THEN amount ELSE 0 END),0) AS inc,
                            COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) AS exp
                            FROM finance""").fetchone()

    s_m = _num(s["m"]); s_q = _num(s["q"]); s_k = _num(s["k"])
    acc = (s_k/s_q*100) if s_q else 0
    score = min(100, round(
        min(30, _num(s["m"])/60/14*30) +
        min(20, _num(g["avg"])*0.20) +
        min(15, _num(m["avg"])*0.15) +
        (15 if s_q and acc >= 80 else 8 if s_q and acc >= 60 else 0) +
        10 + 10, 1))

    clear(); header("ANALYTICS", f"v{VERSION} | Last {days} days")
    print(f"\n  Study: {s_m/60:.1f}h | {int(s_q)} Q | {int(s_k)} correct | {acc:.1f}%")
    print(f"  Goals: {g['t']} total, {g['done']} done, avg {g['avg']:.1f}%")
    print(f"  Missions: {m['t']} total, {m['done']} done, avg {m['avg']:.1f}%")
    print(f"  Income {_num(f['inc']):,.2f}   Expense {_num(f['exp']):,.2f}")
    col = GREEN if score>=70 else YELLOW if score>=40 else RED
    print(f"\n  {c(f'PERFORMANCE SCORE: {score}/100', BOLD+col)}")

def main():
    report(7)
    pause()

run = main
