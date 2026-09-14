"""Admin department - calendar, notes, scheduling, errands."""
from datetime import date, datetime
from ..department import Department
from ...database import fetch_one, fetch_all, execute
from ...guardian import audit


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


class Admin(Department):
    NAME = "admin"
    ROLE = "administrator"
    MANDATE = "Calendar, notes, scheduling, personal errands"
    CAPABILITIES = ("admin", "calendar", "schedule", "note",
                    "appointment", "brief")
    PRIORITY = 3

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "brief":           self._brief,
            "schedule":        self._schedule,
            "note_add":        self._note_add,
            "note_list":       self._note_list,
            "appointment_add": self._appt_add,
            "appointment_list":self._appt_list,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Admin cannot handle '{command}'")
        return fn(args, actor)

    def _brief(self, args, actor):
        today = str(date.today())
        h = datetime.now().hour
        g = ("Good morning" if h < 12 else
             "Good afternoon" if h < 17 else
             "Good evening" if h < 22 else "Late night")
        return {
            "date": today,
            "greeting": g,
            "tasks_pending": int(_q(
                "SELECT COUNT(*) FROM tasks WHERE status IN "
                "('pending','in_progress')")),
            "tasks_overdue": int(_q(
                "SELECT COUNT(*) FROM tasks WHERE status IN "
                "('pending','in_progress') AND due_date IS NOT NULL "
                "AND due_date < date('now')")),
            "appointments_today": int(_q(
                f"SELECT COUNT(*) FROM journal WHERE mood='appointment' "
                f"AND entry_date='{today}'")),
        }

    def _schedule(self, args, actor):
        rows = fetch_all(
            """SELECT title, due_date, priority FROM tasks
               WHERE status IN ('pending','in_progress')
               ORDER BY COALESCE(due_date,'9999') LIMIT 10""")
        return [dict(r) for r in rows]

    def _note_add(self, args, actor):
        content = (args.get("content") or "").strip()
        if not content:
            raise ValueError("content required")
        execute(
            """INSERT INTO journal (entry_date, title, content, mood)
               VALUES (?, ?, ?, 'note')""",
            (str(date.today()), args.get("title") or "note", content))
        self.remember("note", content[:200], importance=4)
        audit.log("admin_note_added", actor=self.NAME,
                  payload={"len": len(content)})
        return {"ok": True}

    def _note_list(self, args, actor):
        rows = fetch_all(
            """SELECT id, entry_date, title, substr(content,1,120) AS excerpt
               FROM journal WHERE mood='note'
               ORDER BY entry_date DESC LIMIT 20""")
        return [dict(r) for r in rows]

    def _appt_add(self, args, actor):
        title = (args.get("title") or "").strip()
        when = args.get("when") or str(date.today())
        if not title:
            raise ValueError("title required")
        execute(
            """INSERT INTO journal (entry_date, title, content, mood)
               VALUES (?, ?, ?, 'appointment')""",
            (when, f"Appointment: {title}",
             args.get("notes") or ""))
        self.remember("appointment", f"{when}: {title}", importance=6)
        audit.log("admin_appt_added", actor=self.NAME,
                  payload={"title": title, "when": when})
        return {"ok": True, "title": title, "when": when}

    def _appt_list(self, args, actor):
        rows = fetch_all(
            """SELECT id, entry_date, title FROM journal
               WHERE mood='appointment'
               ORDER BY entry_date DESC LIMIT 20""")
        return [dict(r) for r in rows]
