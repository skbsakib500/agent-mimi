"""Extended API actions for web dashboard."""
from datetime import date


def _ok(**kw):
    return {"ok": True, **kw}


def _err(msg):
    return {"ok": False, "error": msg}


def add_task(p):
    from ..database import execute
    title = (p.get("title") or "").strip()
    if not title:
        return _err("title required")
    priority = (p.get("priority") or "medium").lower()
    if priority not in ("low", "medium", "high", "critical"):
        priority = "medium"
    execute("""INSERT INTO tasks (mission_id, title, description, due_date, priority, status)
               VALUES (NULL, ?, ?, ?, ?, 'pending')""",
            (title, p.get("description") or "",
             p.get("due_date") or None, priority))
    return _ok(message=f"Task '{title}' added.")


def complete_task(p):
    from ..database import execute, fetch_one
    tid = p.get("id")
    if not tid:
        return _err("id required")
    try:
        tid = int(tid)
    except (TypeError, ValueError):
        return _err("id must be integer")
    row = fetch_one("SELECT * FROM tasks WHERE id=?", (tid,))
    if not row:
        return _err("task not found")
    from datetime import datetime
    execute("""UPDATE tasks SET status='completed', completed_at=?
               WHERE id=?""", (datetime.now().isoformat(timespec="seconds"), tid))
    try:
        from ..missions import sync_progress
        if row["mission_id"]:
            sync_progress(row["mission_id"])
    except Exception:
        pass
    try:
        from ..award import award
        award("task_complete", celebrate=False)
    except Exception:
        pass
    return _ok(message=f"Task #{tid} completed (+25 XP).")


def delete_task(p):
    from ..database import execute, fetch_one
    tid = p.get("id")
    if not tid:
        return _err("id required")
    try:
        tid = int(tid)
    except (TypeError, ValueError):
        return _err("id must be integer")
    if not fetch_one("SELECT id FROM tasks WHERE id=?", (tid,)):
        return _err("not found")
    execute("DELETE FROM tasks WHERE id=?", (tid,))
    try:
        from ..database import execute as ex
        ex("""INSERT INTO system_logs (log_type, message)
              VALUES (?, ?)""", ("web_delete", f"task id={tid}"))
    except Exception:
        pass
    return _ok(message=f"Task #{tid} deleted.")


def add_goal(p):
    from ..database import execute
    title = (p.get("title") or "").strip()
    if not title:
        return _err("title required")
    execute("""INSERT INTO goals (title, description, deadline, priority, progress, status)
               VALUES (?, ?, ?, ?, 0, 'active')""",
            (title, p.get("description") or "",
             p.get("deadline") or None,
             (p.get("priority") or "medium").lower()))
    return _ok(message=f"Goal '{title}' created.")


def add_journal(p):
    from ..database import execute
    content = (p.get("content") or "").strip()
    if not content:
        return _err("content required")
    execute("""INSERT INTO journal (entry_date, title, content, mood)
               VALUES (?, ?, ?, ?)""",
            (p.get("entry_date") or str(date.today()),
             p.get("title") or "", content, p.get("mood") or ""))
    return _ok(message="Journal entry saved.")


def add_study(p):
    from ..database import execute
    subject = (p.get("subject") or "").strip()
    if not subject:
        return _err("subject required")
    try:
        dur = int(p.get("duration_minutes") or 0)
    except (TypeError, ValueError):
        dur = 0
    try:
        q = int(p.get("questions_solved") or 0)
        k = int(p.get("correct_answers") or 0)
    except (TypeError, ValueError):
        q, k = 0, 0
    if k > q:
        return _err("correct answers cannot exceed questions")
    execute("""INSERT INTO study_sessions
               (subject, study_date, duration_minutes, questions_solved,
                correct_answers, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (subject, p.get("study_date") or str(date.today()),
             dur, q, k, p.get("notes") or ""))
    try:
        from ..award import award
        award("study_hour", amount=int((dur / 60.0) * 15), celebrate=False)
    except Exception:
        pass
    return _ok(message=f"Study session '{subject}' logged.")


HANDLERS = {
    "task_add":      add_task,
    "task_complete": complete_task,
    "task_delete":   delete_task,
    "goal_add":      add_goal,
    "journal_add":   add_journal,
    "study_add":     add_study,
}


def handle(payload):
    action = (payload.get("action") or "").strip()
    fn = HANDLERS.get(action)
    if not fn:
        return _err(f"unknown action: {action}")
    try:
        return fn(payload)
    except Exception as e:
        return _err(f"{type(e).__name__}: {e}")
