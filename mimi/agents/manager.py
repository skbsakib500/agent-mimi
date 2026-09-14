"""Manager - tasks, missions, projects."""
from datetime import date, datetime
from .base import Specialist
from ..database import fetch_one, fetch_all, execute
from ..guardian import audit


class Manager(Specialist):
    NAME = "manager"
    ROLE = "manager"
    CAPABILITIES = ("tasks", "missions", "projects", "goals")
    DESCRIPTION = "Task, mission and project management"

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "add_task": self._add_task,
            "list_tasks": self._list_tasks,
            "complete_task": self._complete_task,
            "delete_task": self._delete_task,
            "add_goal": self._add_goal,
            "list_goals": self._list_goals,
            "add_mission": self._add_mission,
            "list_missions": self._list_missions,
        }
        fn = table.get(command)
        if not fn:
            raise ValueError(f"Manager does not handle '{command}'")
        return fn(args, actor)

    def _add_task(self, args, actor):
        title = (args.get("title") or "").strip()
        if not title:
            raise ValueError("title required")
        due = args.get("due_date") or None
        priority = (args.get("priority") or "medium").lower()
        if priority not in ("low", "medium", "high", "critical"):
            priority = "medium"
        execute(
            """INSERT INTO tasks (mission_id, title, description,
               due_date, priority, status)
               VALUES (NULL, ?, ?, ?, ?, 'pending')""",
            (title, args.get("description") or "", due, priority))
        audit.log("manager_task_added", actor="manager",
                  payload={"title": title, "priority": priority})
        return {"ok": True, "title": title, "priority": priority}

    def _list_tasks(self, args, actor):
        limit = int(args.get("limit") or 20)
        rows = fetch_all(
            """SELECT id, title, due_date, priority, status FROM tasks
               WHERE status IN ('pending','in_progress')
               ORDER BY CASE priority
                 WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                 WHEN 'medium' THEN 3 ELSE 4 END,
               COALESCE(due_date,'9999') LIMIT ?""", (limit,))
        return [dict(r) for r in rows]

    def _complete_task(self, args, actor):
        tid = args.get("id")
        if not tid:
            raise ValueError("id required")
        row = fetch_one("SELECT * FROM tasks WHERE id=?", (int(tid),))
        if not row:
            raise ValueError("task not found")
        now = datetime.now().isoformat(timespec="seconds")
        execute("UPDATE tasks SET status='completed', completed_at=? WHERE id=?",
                (now, int(tid)))
        # Sync mission progress if linked
        try:
            if row["mission_id"]:
                from ..missions import sync_progress
                sync_progress(row["mission_id"])
        except Exception:
            pass
        audit.log("manager_task_completed", actor="manager",
                  payload={"id": int(tid)})
        return {"ok": True, "id": int(tid)}

    def _delete_task(self, args, actor):
        tid = args.get("id")
        if not tid:
            raise ValueError("id required")
        execute("DELETE FROM tasks WHERE id=?", (int(tid),))
        audit.log("manager_task_deleted", actor="manager",
                  payload={"id": int(tid)})
        return {"ok": True, "id": int(tid)}

    def _add_goal(self, args, actor):
        title = (args.get("title") or "").strip()
        if not title:
            raise ValueError("title required")
        execute(
            """INSERT INTO goals (title, description, deadline, priority,
               progress, status) VALUES (?, ?, ?, ?, 0, 'active')""",
            (title, args.get("description") or "",
             args.get("deadline") or None,
             (args.get("priority") or "medium").lower()))
        audit.log("manager_goal_added", actor="manager",
                  payload={"title": title})
        return {"ok": True, "title": title}

    def _list_goals(self, args, actor):
        rows = fetch_all(
            """SELECT id, title, progress, priority, status FROM goals
               WHERE status='active' ORDER BY id DESC LIMIT 20""")
        return [dict(r) for r in rows]

    def _add_mission(self, args, actor):
        title = (args.get("title") or "").strip()
        if not title:
            raise ValueError("title required")
        execute(
            """INSERT INTO missions (goal_id, title, description, deadline,
               priority, progress, status) VALUES (?, ?, ?, ?, ?, 0, 'active')""",
            (args.get("goal_id") or None, title,
             args.get("description") or "",
             args.get("deadline") or None,
             (args.get("priority") or "medium").lower()))
        return {"ok": True, "title": title}

    def _list_missions(self, args, actor):
        rows = fetch_all(
            """SELECT id, title, progress, status FROM missions
               WHERE status='active' ORDER BY id DESC LIMIT 20""")
        return [dict(r) for r in rows]


manager = Manager()
