"""Health department - sleep, exercise, food, medicine."""
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


def _ensure_tables():
    execute("""CREATE TABLE IF NOT EXISTS health_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_date TEXT NOT NULL,
        kind TEXT NOT NULL,
        value TEXT,
        amount REAL DEFAULT 0,
        unit TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


class Health(Department):
    NAME = "health"
    ROLE = "health_coach"
    MANDATE = "Track sleep, exercise, food, medicine"
    CAPABILITIES = ("health", "sleep", "exercise", "food",
                    "medicine", "workout", "wellness")
    PRIORITY = 4

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        _ensure_tables()
        table = {
            "health_log":       self._log,
            "health_summary":   self._summary,
            "sleep_avg":        self._sleep,
            "medicine_add":     self._med,
            "medicine_list":    self._med_list,
            "exercise_add":     self._ex,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Health cannot handle '{command}'")
        return fn(args, actor)

    def _log(self, args, actor):
        kind = (args.get("kind") or "").strip().lower()
        if kind not in ("sleep", "exercise", "food", "medicine", "mood"):
            raise ValueError("kind must be sleep/exercise/food/medicine/mood")
        d = args.get("date") or str(date.today())
        value = (args.get("value") or "").strip()
        try:
            amt = float(args.get("amount") or 0)
        except (TypeError, ValueError):
            amt = 0
        unit = (args.get("unit") or "").strip()
        notes = (args.get("notes") or "").strip()
        execute(
            """INSERT INTO health_log
               (log_date, kind, value, amount, unit, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (d, kind, value, amt, unit, notes))
        self.remember(kind, f"{value} {amt}{unit}", importance=3)
        audit.log(f"health_{kind}", actor=self.NAME,
                  payload={"amount": amt, "unit": unit})
        return {"ok": True, "kind": kind}

    def _ex(self, args, actor):
        args = dict(args)
        args["kind"] = "exercise"
        return self._log(args, actor)

    def _med(self, args, actor):
        name = (args.get("name") or "").strip()
        if not name:
            raise ValueError("name required")
        args = dict(args)
        args["kind"] = "medicine"
        args["value"] = name
        return self._log(args, actor)

    def _med_list(self, args, actor):
        rows = fetch_all(
            """SELECT id, log_date, value, notes FROM health_log
               WHERE kind='medicine' ORDER BY log_date DESC LIMIT 20""")
        return [dict(r) for r in rows]

    def _sleep(self, args, actor):
        try:
            avg_min = _q("""SELECT COALESCE(AVG(duration_minutes),0)
                            FROM sleep WHERE sleep_date >= date('now','-6 days')""")
        except Exception:
            avg_min = 0
        return {"avg_hours": round(float(avg_min) / 60, 2)}

    def _summary(self, args, actor):
        sleep = self._sleep(args, actor)
        # last 7d from health_log
        rows = fetch_all(
            """SELECT kind, COUNT(*) AS n, COALESCE(SUM(amount),0) AS total
               FROM health_log
               WHERE log_date >= date('now','-6 days')
               GROUP BY kind""")
        by_kind = {r["kind"]: {"count": r["n"], "total": r["total"]}
                   for r in rows}
        return {
            "sleep_avg_hours": sleep["avg_hours"],
            "exercise_7d": by_kind.get("exercise", {}),
            "medicine_7d": by_kind.get("medicine", {}),
            "food_7d": by_kind.get("food", {}),
            "mood_7d": by_kind.get("mood", {}),
        }
