"""Legal department - research, drafting, case tracking."""
from datetime import date
from ..department import Department
from ...database import execute, fetch_all
from ...guardian import audit


class Legal(Department):
    NAME = "legal"
    ROLE = "legal_assistant"
    MANDATE = "Research notes, document drafts, case tracking (not advice)"
    CAPABILITIES = ("legal", "law", "case", "contract", "research")
    PRIORITY = 6

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "legal_lookup":     self._lookup,
            "legal_draft":      self._draft,
            "legal_case_add":   self._case_add,
            "legal_case_list":  self._case_list,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Legal cannot handle '{command}'")
        return fn(args, actor)

    def _lookup(self, args, actor):
        kw = (args.get("query") or "").strip()
        if not kw:
            raise ValueError("query required")
        rows = fetch_all(
            """SELECT id, entry_date, title, substr(content,1,200) AS excerpt
               FROM journal
               WHERE mood='legal_note' AND (title LIKE ? OR content LIKE ?)
               ORDER BY entry_date DESC LIMIT 10""",
            (f"%{kw}%", f"%{kw}%"))
        return {
            "query": kw,
            "matches": [dict(r) for r in rows],
            "disclaimer": "not legal advice; verify with a lawyer",
        }

    def _draft(self, args, actor):
        title = (args.get("title") or "").strip()
        body = (args.get("body") or "").strip()
        if not title or not body:
            raise ValueError("title and body required")
        execute(
            """INSERT INTO journal (entry_date, title, content, mood)
               VALUES (?, ?, ?, 'legal_draft')""",
            (args.get("date") or str(date.today()), title, body))
        audit.log("legal_draft_saved", actor=self.NAME,
                  payload={"title": title})
        return {"ok": True, "title": title,
                "disclaimer": "draft only; needs lawyer review"}

    def _case_add(self, args, actor):
        title = (args.get("title") or "").strip()
        if not title:
            raise ValueError("title required")
        execute(
            """INSERT INTO journal (entry_date, title, content, mood)
               VALUES (?, ?, ?, 'legal_case')""",
            (args.get("date") or str(date.today()),
             f"Case: {title}", args.get("notes") or ""))
        self.remember("case", title, importance=7)
        return {"ok": True, "title": title}

    def _case_list(self, args, actor):
        rows = fetch_all(
            """SELECT id, entry_date, title FROM journal
               WHERE mood='legal_case' ORDER BY entry_date DESC LIMIT 30""")
        return [dict(r) for r in rows]
