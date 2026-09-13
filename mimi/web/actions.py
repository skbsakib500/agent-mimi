"""POST actions for web dashboard."""

def handle_add(payload):
    kind = (payload.get("kind") or "").strip().lower()
    if kind == "task":
        return _add_task(payload)
    if kind == "goal":
        return _add_goal(payload)
    if kind == "journal":
        return _add_journal(payload)
    return {"ok": False, "error": "unknown kind"}


def _add_task(p):
    from ..database import execute
    title = (p.get("title") or "").strip()
    if not title:
        return {"ok": False, "error": "title required"}
    execute("""INSERT INTO tasks (mission_id, title, description, due_date, priority, status)
               VALUES (NULL, ?, ?, ?, ?, 'pending')""",
            (title, p.get("description") or "",
             p.get("due_date") or None,
             p.get("priority") or "medium"))
    return {"ok": True}


def _add_goal(p):
    from ..database import execute
    title = (p.get("title") or "").strip()
    if not title:
        return {"ok": False, "error": "title required"}
    execute("""INSERT INTO goals (title, description, deadline, priority, progress, status)
               VALUES (?, ?, ?, ?, 0, 'active')""",
            (title, p.get("description") or "",
             p.get("deadline") or None,
             p.get("priority") or "medium"))
    return {"ok": True}


def _add_journal(p):
    from ..database import execute
    from datetime import date
    content = (p.get("content") or "").strip()
    if not content:
        return {"ok": False, "error": "content required"}
    execute("""INSERT INTO journal (entry_date, title, content, mood)
               VALUES (?, ?, ?, ?)""",
            (p.get("entry_date") or str(date.today()),
             p.get("title") or "",
             content,
             p.get("mood") or ""))
    return {"ok": True}
