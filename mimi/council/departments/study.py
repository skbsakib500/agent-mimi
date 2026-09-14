"""Study department - syllabus, exams, revisions."""
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


class Study(Department):
    NAME = "study"
    ROLE = "study_manager"
    MANDATE = "Track study sessions, syllabus, revision, exam prep"
    CAPABILITIES = ("study", "syllabus", "exam", "revision",
                    "learning", "practice")
    PRIORITY = 4

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "study_log":      self._log,
            "study_summary":  self._summary,
            "study_plan":     self._plan,
            "revision_list":  self._revision,
            "weak_subjects":  self._weak,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Study cannot handle '{command}'")
        return fn(args, actor)

    def _log(self, args, actor):
        subject = (args.get("subject") or "").strip()
        if not subject:
            raise ValueError("subject required")
        try:
            dur = int(args.get("duration_minutes") or 0)
            q = int(args.get("questions") or 0)
            k = int(args.get("correct") or 0)
        except (TypeError, ValueError):
            dur = q = k = 0
        if k > q:
            raise ValueError("correct > questions")
        execute(
            """INSERT INTO study_sessions
               (subject, study_date, duration_minutes,
                questions_solved, correct_answers, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (subject, args.get("date") or str(date.today()),
             dur, q, k, args.get("notes") or ""))
        acc = (k / q * 100) if q else 0
        self.remember("session", f"{subject} {dur}min acc={acc:.0f}%",
                      importance=4)
        audit.log("study_logged", actor=self.NAME,
                  payload={"subject": subject, "min": dur})
        return {"ok": True, "subject": subject,
                "duration": dur, "accuracy": round(acc, 1)}

    def _summary(self, args, actor):
        r = fetch_one(
            """SELECT COUNT(*) AS n,
               COALESCE(SUM(duration_minutes),0) AS m,
               COALESCE(SUM(questions_solved),0) AS q,
               COALESCE(SUM(correct_answers),0) AS k
               FROM study_sessions
               WHERE study_date >= date('now','-6 days')""")
        r = dict(r) if r else {}
        n = r.get("n") or 0
        m = r.get("m") or 0
        q = r.get("q") or 0
        k = r.get("k") or 0
        acc = (k / q * 100) if q else 0
        return {
            "sessions_7d": n, "minutes_7d": m,
            "hours_7d": round(m / 60, 2),
            "questions": q, "correct": k,
            "accuracy": round(acc, 1),
        }

    def _plan(self, args, actor):
        s = self._summary({}, actor)
        plan = []
        if s["hours_7d"] < 7:
            plan.append("Two 2-hour blocks this week.")
        if s["accuracy"] and s["accuracy"] < 70:
            plan.append("Revisit incorrect answers before new topics.")
        weak = self._weak({}, actor)
        for w in weak[:2]:
            plan.append(f"Focus: {w['subject']} (acc {w['acc']}%)")
        if not plan:
            plan.append("Maintain 7h/week rhythm; increase difficulty.")
        return {"plan": plan, "context": s}

    def _weak(self, args, actor):
        rows = fetch_all(
            """SELECT subject,
               SUM(questions_solved) AS q,
               SUM(correct_answers) AS k
               FROM study_sessions
               WHERE study_date >= date('now','-29 days')
               AND questions_solved > 0
               GROUP BY subject""")
        out = []
        for r in rows:
            q = r["q"] or 0
            k = r["k"] or 0
            if q:
                acc = k / q * 100
                if acc < 75:
                    out.append({"subject": r["subject"],
                                "acc": round(acc, 1), "n": q})
        out.sort(key=lambda x: x["acc"])
        return out

    def _revision(self, args, actor):
        rows = fetch_all(
            """SELECT subject, SUM(duration_minutes) AS m
               FROM study_sessions
               WHERE study_date >= date('now','-29 days')
               GROUP BY subject ORDER BY m ASC LIMIT 5""")
        return [{"subject": r["subject"], "minutes": r["m"]}
                for r in rows]
