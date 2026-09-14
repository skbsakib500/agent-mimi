"""Advisor - decision support and strategy."""
from datetime import date, datetime
from .base import Specialist
from ..database import fetch_one, fetch_all
from ..guardian import audit


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


class Advisor(Specialist):
    NAME = "advisor"
    ROLE = "advisor"
    CAPABILITIES = ("advisor", "advice", "strategy", "plan")
    DESCRIPTION = "Strategy, decision support, daily plan"

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        if command in ("advice", "strategy"):
            return self._advice(args)
        if command == "plan":
            return self._plan(args)
        raise ValueError(f"Advisor does not handle '{command}'")

    def _advice(self, args):
        """Weighted decision matrix.

        args: {
          "question": "...",
          "options": [{"name": "...", "scores": {"cost": 8, "impact": 7, ...}}],
          "weights": {"cost": 0.3, "impact": 0.7}
        }
        """
        q = args.get("question") or "(no question)"
        options = args.get("options") or []
        weights = args.get("weights") or {}
        if not isinstance(options, list) or not options:
            raise ValueError("options required")
        if not weights:
            raise ValueError("weights required (criteria -> weight)")

        scored = []
        for opt in options:
            s = opt.get("scores") or {}
            total = 0.0
            for k, w in weights.items():
                try:
                    total += float(s.get(k, 0)) * float(w)
                except (TypeError, ValueError):
                    pass
            scored.append({"name": opt.get("name") or "?",
                           "score": round(total, 2)})
        scored.sort(key=lambda x: -x["score"])
        top = scored[0] if scored else None
        return {
            "question": q,
            "weights": weights,
            "ranking": scored,
            "recommendation": top["name"] if top else None,
            "rationale": (
                f"'{top['name']}' maximizes weighted score "
                f"({top['score']}) under chosen weights."
                if top else "no options"),
        }

    def _plan(self, args):
        """Return a lightweight daily plan from current data."""
        tasks_p = int(_q("SELECT COUNT(*) FROM tasks WHERE status IN "
                         "('pending','in_progress')"))
        over = int(_q("SELECT COUNT(*) FROM tasks WHERE status IN "
                      "('pending','in_progress') AND due_date IS NOT NULL "
                      "AND due_date < date('now')"))
        study_h = float(_q("SELECT COALESCE(SUM(duration_minutes),0)/60.0 "
                           "FROM study_sessions WHERE study_date >= "
                           "date('now','-6 days')"))
        bal = float(_q(
            "SELECT COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END),0) - "
            "COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) "
            "FROM finance"))
        blocks = []
        if over > 0:
            blocks.append({"when": "morning",
                           "action": f"clear {over} overdue task(s)"})
        blocks.append({"when": "focus",
                       "action": "deepest task in first 90 min"})
        if study_h < 7:
            blocks.append({"when": "afternoon",
                           "action": f"study (week {study_h:.1f}h / 7h)"})
        if bal < 0:
            blocks.append({"when": "evening",
                           "action": "review expenses and cut one item"})
        blocks.append({"when": "evening",
                       "action": "journal + plan tomorrow's top 3"})
        return {
            "date": str(date.today()),
            "context": {"tasks_pending": tasks_p, "overdue": over,
                        "study_week_h": study_h, "balance": bal},
            "plan": blocks,
            "one_rule": "Do the hardest thing before noon.",
        }


advisor = Advisor()
