"""AI-powered weekly review."""
from datetime import date, datetime, timedelta
from .database import fetch_one, fetch_all
from .ai_context import snapshot
from .llm import load_provider


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


def gather_week():
    """Numbers that should appear in the review."""
    return {
        "study_hours": _q("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
                             FROM study_sessions
                             WHERE study_date >= date('now','-6 days')"""),
        "study_sessions": _q("""SELECT COUNT(*) FROM study_sessions
                                WHERE study_date >= date('now','-6 days')"""),
        "tasks_completed": _q("""SELECT COUNT(*) FROM tasks
                                 WHERE status='completed'
                                 AND completed_at >= date('now','-6 days')"""),
        "tasks_overdue": _q("""SELECT COUNT(*) FROM tasks
                              WHERE status IN ('pending','in_progress')
                              AND due_date IS NOT NULL AND due_date < date('now')"""),
        "income": _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='income'"),
        "expense": _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='expense'"),
        "sleep_avg": _q("""SELECT COALESCE(AVG(duration_minutes),0)/60.0 FROM sleep
                           WHERE sleep_date >= date('now','-6 days')"""),
        "journal_count": _q("""SELECT COUNT(*) FROM journal
                               WHERE entry_date >= date('now','-6 days')"""),
        "goals_active": _q("SELECT COUNT(*) FROM goals WHERE status='active'"),
        "goals_avg": _q("SELECT COALESCE(AVG(progress),0) FROM goals WHERE status='active'"),
    }


PROMPT = """You are Mimi reviewing {user}'s past week.

WEEK NUMBERS:
{numbers}

Write a short weekly review with EXACTLY these sections:

## Wins
- 2-3 bullets of what went well (reference numbers)

## Warnings
- 2-3 bullets of concerns (reference numbers)

## Focus Next Week
- 3 concrete actions for the coming week

## One Line
A single sentence summary of the week.

Rules:
- 200 words max total
- Warm, direct tone
- No filler
- Use the real numbers
"""


def build_prompt():
    try:
        from .core import USER_NAME
    except Exception:
        USER_NAME = "SKB Sakib"

    w = gather_week()
    numbers = (
        f"Study: {w['study_hours']:.1f}h in {w['study_sessions']} sessions\n"
        f"Tasks completed: {w['tasks_completed']}\n"
        f"Tasks overdue: {w['tasks_overdue']}\n"
        f"Income: {w['income']:,.0f} | Expense: {w['expense']:,.0f} | "
        f"Balance: {w['income']-w['expense']:,.0f}\n"
        f"Sleep avg: {w['sleep_avg']:.1f}h\n"
        f"Journal entries: {w['journal_count']}\n"
        f"Goals active: {w['goals_active']} (avg progress {w['goals_avg']:.0f}%)\n"
    )
    return PROMPT.format(user=USER_NAME, numbers=numbers), w


def offline_review(w):
    """Fallback review when no LLM is available."""
    wins = []
    warns = []
    focus = []

    if w["study_hours"] >= 7:
        wins.append(f"Study hit {w['study_hours']:.1f}h — above target.")
    elif w["study_hours"] >= 3:
        warns.append(f"Study at {w['study_hours']:.1f}h — below 7h target.")
    else:
        warns.append(f"Study at {w['study_hours']:.1f}h — very low.")

    if w["tasks_completed"] >= 5:
        wins.append(f"{w['tasks_completed']} tasks completed — strong output.")
    elif w["tasks_completed"] == 0:
        warns.append("No tasks completed this week.")

    if w["tasks_overdue"] > 0:
        warns.append(f"{w['tasks_overdue']} overdue task(s) — clear them first.")

    if w["sleep_avg"] >= 7:
        wins.append(f"Sleep avg {w['sleep_avg']:.1f}h — recovery is solid.")
    elif w["sleep_avg"] and w["sleep_avg"] < 6:
        warns.append(f"Sleep avg {w['sleep_avg']:.1f}h — too low for focus.")

    if w["income"] - w["expense"] >= 0:
        wins.append("Cash flow positive.")
    else:
        warns.append(f"Cash flow negative by {abs(w['income']-w['expense']):,.0f}.")

    if w["study_hours"] < 7:
        focus.append("Two 2-hour study blocks this week.")
    if w["tasks_overdue"]:
        focus.append("Clear overdue tasks first.")
    if w["sleep_avg"] and w["sleep_avg"] < 7:
        focus.append("Sleep 7h+ for 5 nights.")
    if len(focus) < 3:
        focus.append("Keep journaling daily.")
    if len(focus) < 3:
        focus.append("Review goals and update progress.")

    lines = ["## Wins"]
    lines += [f"- {x}" for x in wins] or ["- (no wins logged yet)"]
    lines += ["", "## Warnings"]
    lines += [f"- {x}" for x in warns] or ["- (nothing critical)"]
    lines += ["", "## Focus Next Week"]
    lines += [f"- {x}" for x in focus[:3]]
    lines += ["", "## One Line"]
    lines.append("Steady progress, tighten consistency where the numbers are weakest.")
    return "\n".join(lines)


def review():
    prompt, w = build_prompt()
    llm = load_provider()
    if llm:
        try:
            out = llm.chat(prompt, [{"role": "user", "content": "Write the review."}],
                           max_tokens=500, temperature=0.5)
            if out and not out.startswith("[LLM"):
                return out, w, "AI"
        except Exception:
            pass
    return offline_review(w), w, "offline"


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
                     c, clear, header, pause, section)
    clear()
    header("📋 WEEKLY REVIEW", "AI-powered · last 7 days")
    print(c("\n  Generating...", DIM + WHITE))
    text, w, source = review()

    clear()
    header("📋 WEEKLY REVIEW", f"last 7 days · {source}")
    section("NUMBERS", "📊")
    print(f"  Study   : {w['study_hours']:.1f}h in {w['study_sessions']} sessions")
    print(f"  Tasks   : {w['tasks_completed']} done, {w['tasks_overdue']} overdue")
    print(f"  Balance : {w['income']-w['expense']:,.0f}")
    print(f"  Sleep   : {w['sleep_avg']:.1f}h avg")
    print(f"  Journal : {w['journal_count']} entries")
    section("REVIEW", "📝")
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
        f = d / f"review_{date.today().isoformat()}.md"
        f.write_text(text, encoding="utf-8")
        print(c(f"\n  Saved: {f}", GREEN))
    pause()

run = main
