"""Personal Assistant - briefings, notes, schedule glance."""
from datetime import date, datetime
from .base import Specialist
from ..database import fetch_one, fetch_all, execute
from ..guardian import audit


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


class PA(Specialist):
    NAME = "pa"
    ROLE = "personal_assistant"
    CAPABILITIES = ("pa", "brief", "notes", "schedule")
    DESCRIPTION = "Personal assistant - briefing, notes, schedule glance"

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        if command == "brief":
            return self._brief()
        if command == "schedule":
            return self._schedule()
        if command == "notes":
            return self._notes(args)
        raise ValueError(f"PA does not handle '{command}'")

    def _brief(self):
        today = str(date.today())
        return {
            "date": today,
            "greeting": self._greeting(),
            "tasks_pending": _q(
                "SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')"),
            "tasks_overdue": _q(
                "SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress') "
                "AND due_date IS NOT NULL AND due_date < date('now')"),
            "tasks_today": _q(
                "SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress') "
                "AND due_date = date('now')"),
            "study_week_h": float(_q(
                "SELECT COALESCE(SUM(duration_minutes),0)/60.0 FROM study_sessions "
                "WHERE study_date >= date('now','-6 days')")),
            "balance": float(_q(
                "SELECT COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END),0) - "
                "COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) "
                "FROM finance")),
            "journal_today": _q(
                f"SELECT COUNT(*) FROM journal WHERE entry_date='{today}'"),
            "daily_today": _q(
                f"SELECT COUNT(*) FROM daily_logs WHERE log_date='{today}'"),
        }

    def _greeting(self):
        h = datetime.now().hour
        if h < 12:
            return "Good morning"
        if h < 17:
            return "Good afternoon"
        if h < 22:
            return "Good evening"
        return "Late night"

    def _schedule(self):
        rows = fetch_all(
            """SELECT title, due_date, priority FROM tasks
               WHERE status IN ('pending','in_progress')
               ORDER BY COALESCE(due_date,'9999') LIMIT 10""")
        return [dict(r) for r in rows]

    def _notes(self, args):
        """List or add a quick note (stored in journal with tag 'note')."""
        action = (args.get("action") or "list").lower()
        if action == "add":
            content = (args.get("content") or "").strip()
            if not content:
                raise ValueError("note content required")
            execute(
                """INSERT INTO journal (entry_date, title, content, mood)
                   VALUES (?, ?, ?, ?)""",
                (str(date.today()), args.get("title") or "quick note",
                 content, "note"))
            audit.log("pa_note_added", actor="pa",
                      payload={"len": len(content)})
            return {"ok": True, "added": True}
        rows = fetch_all(
            """SELECT id, entry_date, title FROM journal
               WHERE mood='note' ORDER BY entry_date DESC LIMIT 20""")
        return [dict(r) for r in rows]


# Auto-register when imported
pa = PA()
