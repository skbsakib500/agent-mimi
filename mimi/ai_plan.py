"""AI-generated daily plan."""
from datetime import date, datetime
from .database import fetch_one, fetch_all
from .llm import load_provider


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


def _rows(sql, limit=10):
    try:
        return [dict(r) for r in fetch_all(sql)[:limit]]
    except Exception:
        return []


def gather():
    return {
        "date": date.today().isoformat(),
        "tasks": _rows("""SELECT title, due_date, priority FROM tasks
                          WHERE status IN ('pending','in_progress')
                          ORDER BY CASE priority
                            WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3 ELSE 4 END,
                          COALESCE(due_date,'9999') LIMIT 10"""),
        "overdue": _q("""SELECT COUNT(*) FROM tasks
                         WHERE status IN ('pending','in_progress')
                         AND due_date IS NOT NULL AND due_date < date('now')"""),
        "study_today": _q("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
                             FROM study_sessions WHERE study_date=date('now')"""),
        "study_week": _q("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
                            FROM study_sessions
                            WHERE study_date >= date('now','-6 days')"""),
        "goals_urgent": _rows("""SELECT title, progress, deadline FROM goals
                                 WHERE status='active' AND deadline IS NOT NULL
                                 AND deadline BETWEEN date('now') AND date('now','+7 day')
                                 ORDER BY deadline LIMIT 3"""),
        "sleep_avg": _q("""SELECT COALESCE(AVG(duration_minutes),0)/60.0
                           FROM sleep WHERE sleep_date >= date('now','-6 days')"""),
        "energy": _q("""SELECT energy FROM daily_logs
                        WHERE log_date=date('now') LIMIT 1"""),
        "weather": _maybe_weather(),
    }


def _maybe_weather():
    try:
        from .api_weather import available, current
        if not available():
            return None
        c = current("Dhaka")
        if not c:
            return None
        return f"{c['temp']:.0f}C {c['desc']}"
    except Exception:
        return None


PROMPT = """You are Mimi, planning {user}'s day.

TODAY: {date}
Weather: {weather}
Energy: {energy}/10
Sleep avg (7d): {sleep:.1f}h
Overdue tasks: {overdue}
Study so far today: {study_today:.1f}h
Study this week: {study_week:.1f}h (target 7h)

PENDING TASKS:
{tasks}

GOALS DUE THIS WEEK:
{goals}

Write a concrete plan for today. Use EXACTLY these sections:

## Morning
- 2-3 bullets

## Focus Block
- 2-3 bullets (deep work; what to do first)

## Afternoon
- 2-3 bullets

## Evening
- 2-3 bullets

## One Rule
Single sentence: the most important constraint for today.

Rules:
- Specific times like 9:00-11:00
- Reference actual task titles
- Max 200 words
- Warm but direct
"""


def build_prompt():
    try:
        from .core import USER_NAME
    except Exception:
        USER_NAME = "SKB Sakib"
    g = gather()

    tasks_text = "\n".join(
        f"- {t['title']} [due {t['due_date'] or '-'}, {t['priority']}]"
        for t in g["tasks"]) or "(none)"
    goals_text = "\n".join(
        f"- {x['title']} ({x['progress']}%, due {x['deadline']})"
        for x in g["goals_urgent"]) or "(none)"

    return PROMPT.format(
        user=USER_NAME, date=g["date"],
        weather=g["weather"] or "unknown",
        energy=g["energy"] or 5,
        sleep=g["sleep_avg"], overdue=g["overdue"],
        study_today=g["study_today"], study_week=g["study_week"],
        tasks=tasks_text, goals=goals_text), g


def offline_plan(g):
    lines = ["## Morning"]
    if g["overdue"]:
        lines.append(f"- Clear {g['overdue']} overdue task(s) first.")
    lines.append("- Start with 5 min of review: goals + today's tasks.")
    lines.append("- Log yesterday's sleep + daily if not done.")

    lines += ["", "## Focus Block"]
    top = g["tasks"][:2] if g["tasks"] else []
    if top:
        for t in top:
            lines.append(f"- 25 min: {t['title']}")
    else:
        lines.append("- 25 min: highest-impact goal work.")
    if g["study_week"] < 7:
        lines.append(f"- Then 50 min study (week at {g['study_week']:.1f}h / 7h).")

    lines += ["", "## Afternoon"]
    lines.append("- 30 min: incoming messages + small tasks.")
    lines.append("- 15 min walk if possible.")
    lines.append("- Update progress on any active goal.")

    lines += ["", "## Evening"]
    lines.append("- Journal a few lines about today.")
    lines.append("- Prep tomorrow's top 3 tasks.")
    lines.append("- Sleep 7h+ if possible.")

    lines += ["", "## One Rule"]
    lines.append("Do the hardest task before noon.")
    return "\n".join(lines)


def plan():
    prompt, g = build_prompt()
    llm = load_provider()
    if llm:
        try:
            out = llm.chat(prompt,
                           [{"role": "user", "content": "Write the plan."}],
                           max_tokens=500, temperature=0.5)
            if out and not out.startswith("[LLM"):
                return out, g, "AI"
        except Exception:
            pass
    return offline_plan(g), g, "offline"


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    clear()
    header("🗓 AI DAILY PLAN", "Personalized for today")
    print(c("\n  Generating...", DIM + WHITE))
    text, g, source = plan()

    clear()
    header("🗓 AI DAILY PLAN", f"{g['date']} · {source}")
    section("CONTEXT", "📊")
    print(f"  Weather  : {g['weather'] or '-'}")
    print(f"  Energy   : {g['energy'] or 5}/10")
    print(f"  Sleep 7d : {g['sleep_avg']:.1f}h")
    print(f"  Overdue  : {g['overdue']}")
    print(f"  Study 7d : {g['study_week']:.1f}h")
    section("PLAN", "📝")
    for line in text.splitlines():
        if line.startswith("##"):
            print()
            print(c(f"  {line}", BOLD + CYAN))
        elif line.startswith("-"):
            print(c(f"  {line}", WHITE))
        else:
            print(f"  {line}")
    print()
    print("  1. Save to file   0. Back")
    ch = input(c("\n  > Select: ")).strip()
    if ch == "1":
        from pathlib import Path
        from .database import BASE_DIR
        d = Path(BASE_DIR) / "reports"
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"plan_{date.today().isoformat()}.md"
        f.write_text(text, encoding="utf-8")
        print(c(f"\n  Saved: {f}", GREEN))
    pause()

run = main
