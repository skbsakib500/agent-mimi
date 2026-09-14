"""Strategy department - decisions, priorities, long-term planning."""
from datetime import date, datetime, timedelta
from ..department import Department
from ...database import fetch_one, fetch_all, execute
from ...guardian import audit


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


def _ensure_tables():
    execute("""CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        decided_at TEXT DEFAULT CURRENT_TIMESTAMP,
        question TEXT NOT NULL,
        options TEXT,
        chosen TEXT,
        reasoning TEXT,
        review_at TEXT,
        outcome TEXT)""")


class Strategy(Department):
    NAME = "strategy"
    ROLE = "advisor"
    MANDATE = "Decision support, priorities, long-term planning"
    CAPABILITIES = ("strategy", "advice", "decision",
                    "priority", "plan", "review")
    PRIORITY = 2

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        _ensure_tables()
        table = {
            "advice":          self._advice,
            "priority":        self._priority,
            "decision_record": self._record,
            "decision_list":   self._decisions,
            "weekly_review":   self._weekly,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Strategy cannot handle '{command}'")
        return fn(args, actor)

    def _advice(self, args, actor):
        """Weighted decision matrix."""
        q = (args.get("question") or "(no question)").strip()
        options = args.get("options") or []
        weights = args.get("weights") or {}
        if not options or not weights:
            raise ValueError("options and weights required")
        scored = []
        for o in options:
            s = o.get("scores") or {}
            total = 0.0
            for k, w in weights.items():
                try:
                    total += float(s.get(k, 0)) * float(w)
                except (TypeError, ValueError):
                    pass
            scored.append({"name": o.get("name") or "?",
                           "score": round(total, 2)})
        scored.sort(key=lambda x: -x["score"])
        top = scored[0] if scored else None
        # remember for review
        self.remember("decision_advice",
                      f"{q} -> {top['name'] if top else '?'}",
                      importance=6)
        return {
            "question": q, "ranking": scored,
            "recommendation": top["name"] if top else None,
        }

    def _priority(self, args, actor):
        """Rank urgent items across the system."""
        items = []
        overdue = int(_q(
            "SELECT COUNT(*) FROM tasks WHERE status IN "
            "('pending','in_progress') AND due_date IS NOT NULL "
            "AND due_date < date('now')"))
        due_today = int(_q(
            "SELECT COUNT(*) FROM tasks WHERE status IN "
            "('pending','in_progress') AND due_date = date('now')"))
        critical = int(_q(
            "SELECT COUNT(*) FROM tasks WHERE status IN "
            "('pending','in_progress') AND priority='critical'"))
        if overdue:
            items.append({"rank": 1, "why": "overdue tasks",
                          "count": overdue})
        if critical:
            items.append({"rank": 2, "why": "critical tasks",
                          "count": critical})
        if due_today:
            items.append({"rank": 3, "why": "due today",
                          "count": due_today})
        if not items:
            items.append({"rank": 9, "why": "nothing urgent", "count": 0})
        return {"priorities": items,
                "one_rule": "Do the highest-rank item before noon."}

    def _record(self, args, actor):
        q = (args.get("question") or "").strip()
        chosen = (args.get("chosen") or "").strip()
        if not q or not chosen:
            raise ValueError("question and chosen required")
        review = args.get("review_at") or \
                 str(date.today() + timedelta(days=30))
        execute(
            """INSERT INTO decisions
               (question, options, chosen, reasoning, review_at)
               VALUES (?, ?, ?, ?, ?)""",
            (q, str(args.get("options") or ""), chosen,
             args.get("reasoning") or "", review))
        self.remember("decision", f"{q} -> {chosen}", importance=8)
        return {"ok": True, "review_at": review}

    def _decisions(self, args, actor):
        rows = fetch_all(
            """SELECT id, decided_at, question, chosen, review_at, outcome
               FROM decisions ORDER BY id DESC LIMIT 30""")
        return [dict(r) for r in rows]

    def _weekly(self, args, actor):
        # Simple weekly strategy review
        bal = float(_q(
            "SELECT COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END),0) - "
            "COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) "
            "FROM finance"))
        study = float(_q(
            "SELECT COALESCE(SUM(duration_minutes),0)/60.0 FROM study_sessions "
            "WHERE study_date >= date('now','-6 days')"))
        priorities = self._priority({}, actor)
        actions = []
        if study < 7:
            actions.append("Schedule 2 study blocks (target 7h).")
        if bal < 0:
            actions.append("Cut one recurring expense.")
        for p in priorities["priorities"]:
            if p["count"]:
                actions.append(f"Clear {p['why']} ({p['count']}).")
        if not actions:
            actions.append("Maintain rhythm; review goals.")
        return {"actions": actions[:5], "reviewed_at": str(date.today())}
