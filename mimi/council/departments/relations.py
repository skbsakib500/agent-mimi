"""Relations department - family, friends, birthdays, events."""
from datetime import date
from ..department import Department
from ...database import fetch_all, fetch_one, execute
from ...guardian import audit


def _ensure_tables():
    execute("""CREATE TABLE IF NOT EXISTS persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        relation TEXT,
        birthday TEXT,
        phone TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT NOT NULL,
        title TEXT NOT NULL,
        kind TEXT DEFAULT 'event',
        person_id INTEGER,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


class Relations(Department):
    NAME = "relations"
    ROLE = "relations_manager"
    MANDATE = "Family, friends, birthdays, events"
    CAPABILITIES = ("relations", "family", "friend", "birthday",
                    "event", "contact", "gift")
    PRIORITY = 6

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        _ensure_tables()
        table = {
            "person_add":     self._add_person,
            "person_list":    self._list_persons,
            "birthdays":      self._birthdays,
            "event_add":      self._add_event,
            "event_list":     self._list_events,
            "upcoming":       self._upcoming,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Relations cannot handle '{command}'")
        return fn(args, actor)

    def _add_person(self, args, actor):
        name = (args.get("name") or "").strip()
        if not name:
            raise ValueError("name required")
        execute(
            """INSERT INTO persons (name, relation, birthday, phone, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (name, args.get("relation") or "",
             args.get("birthday") or "",
             args.get("phone") or "",
             args.get("notes") or ""))
        self.remember("person", f"{name} ({args.get('relation','')})",
                      importance=6)
        return {"ok": True, "name": name}

    def _list_persons(self, args, actor):
        rows = fetch_all(
            """SELECT id, name, relation, birthday FROM persons
               ORDER BY name LIMIT 100""")
        return [dict(r) for r in rows]

    def _birthdays(self, args, actor):
        rows = fetch_all(
            """SELECT name, relation, birthday FROM persons
               WHERE birthday IS NOT NULL AND birthday != ''
               ORDER BY substr(birthday,6,5)""")
        today = date.today()
        out = []
        for r in rows:
            try:
                bd = r["birthday"]
                m_d = bd[5:10]
                this_year = f"{today.year}-{m_d}"
                import datetime as dt
                bdd = dt.datetime.strptime(this_year, "%Y-%m-%d").date()
                if bdd < today:
                    bdd = bdd.replace(year=today.year + 1)
                days = (bdd - today).days
                out.append({"name": r["name"],
                            "relation": r["relation"],
                            "date": bd, "in_days": days})
            except Exception:
                continue
        out.sort(key=lambda x: x["in_days"])
        return out[:10]

    def _add_event(self, args, actor):
        title = (args.get("title") or "").strip()
        if not title:
            raise ValueError("title required")
        execute(
            """INSERT INTO events (event_date, title, kind, person_id, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (args.get("date") or str(date.today()),
             title, args.get("kind") or "event",
             args.get("person_id") or None,
             args.get("notes") or ""))
        return {"ok": True, "title": title}

    def _list_events(self, args, actor):
        rows = fetch_all(
            """SELECT id, event_date, title, kind FROM events
               ORDER BY event_date DESC LIMIT 30""")
        return [dict(r) for r in rows]

    def _upcoming(self, args, actor):
        rows = fetch_all(
            """SELECT event_date, title, kind FROM events
               WHERE event_date BETWEEN date('now') AND date('now','+30 day')
               ORDER BY event_date LIMIT 20""")
        return [dict(r) for r in rows]
