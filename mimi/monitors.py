"""Agent Mimi - read-only monitors."""
from .database import fetch_one, table_exists


def _one(q, p=()):
    return fetch_one(q, p)


def study_monitor():
    if not table_exists("study_sessions"): return None
    r = _one("""SELECT COALESCE(SUM(duration_minutes),0) AS m
                FROM study_sessions WHERE study_date>=date('now','-6 days')""")
    return {"hours": r["m"] / 60.0}


def goal_monitor():
    if not table_exists("goals"): return None
    r = _one("SELECT COALESCE(AVG(progress),0) AS a FROM goals WHERE status='active'")
    return {"avg_progress": float(r["a"] or 0)}


def mission_monitor():
    if not table_exists("missions"): return None
    r = _one("SELECT COALESCE(AVG(progress),0) AS a FROM missions WHERE status='active'")
    return {"avg_progress": float(r["a"] or 0)}


def task_monitor():
    if not table_exists("tasks"): return None
    o = _one("""SELECT COUNT(*) AS n FROM tasks
                WHERE status IN ('pending','in_progress')
                AND due_date IS NOT NULL AND due_date < date('now')""")["n"]
    s = _one("""SELECT COUNT(*) AS n FROM tasks
                WHERE status IN ('pending','in_progress')
                AND due_date IS NOT NULL
                AND due_date BETWEEN date('now') AND date('now','+1 day')""")["n"]
    return {"overdue": o, "due_soon": s}


def finance_monitor():
    if not table_exists("finance"): return None
    r = _one("""SELECT
        COALESCE(SUM(CASE WHEN transaction_type='income'  THEN amount ELSE 0 END),0) inc,
        COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) exp
        FROM finance""")
    return {"income": float(r["inc"]), "expense": float(r["exp"]),
            "balance": float(r["inc"]) - float(r["exp"])}


def sleep_monitor():
    if not table_exists("sleep"): return None
    r = _one("""SELECT COALESCE(AVG(duration_minutes),0) AS m FROM sleep
                WHERE sleep_date>=date('now','-6 days')""")
    return {"avg_minutes": float(r["m"] or 0)}


def collect():
    return {
        "study": study_monitor(),
        "goals": goal_monitor(),
        "missions": mission_monitor(),
        "tasks": task_monitor(),
        "finance": finance_monitor(),
        "sleep": sleep_monitor(),
    }


def evaluate(metrics):
    from .automation_rules import (study_low, goal_low, mission_low,
                                    task_overdue, task_due_soon,
                                    finance_negative, sleep_low)
    rules = []
    def push(x):
        if x: rules.append(x)

    m = metrics.get("study")
    if m: push(study_low(m["hours"]))
    m = metrics.get("goals")
    if m: push(goal_low(m["avg_progress"]))
    m = metrics.get("missions")
    if m: push(mission_low(m["avg_progress"]))
    m = metrics.get("tasks")
    if m:
        push(task_overdue(m["overdue"]))
        push(task_due_soon(m["due_soon"]))
    m = metrics.get("finance")
    if m: push(finance_negative(m["balance"]))
    m = metrics.get("sleep")
    if m: push(sleep_low(m["avg_minutes"]))
    return rules
