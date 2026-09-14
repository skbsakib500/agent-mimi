"""Research department - authorized web research, notes, citations."""
import re
from datetime import date
from ..department import Department
from ...database import execute, fetch_all
from ...guardian import audit


class Research(Department):
    NAME = "research"
    ROLE = "researcher"
    MANDATE = "Authorized research, summarize findings, cite sources"
    CAPABILITIES = ("research", "search", "lookup", "source",
                    "cite", "fact")
    PRIORITY = 5

    ALLOWED_HOSTS = (
        "wikipedia.org", "github.com", "arxiv.org",
        "news.ycombinator.com", "stackoverflow.com",
        "docs.python.org", "developer.mozilla.org",
    )

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "research_note":   self._note,
            "research_list":   self._list,
            "research_query":  self._query,
            "safe_fetch":      self._fetch,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Research cannot handle '{command}'")
        return fn(args, actor)

    def _note(self, args, actor):
        topic = (args.get("topic") or "").strip()
        summary = (args.get("summary") or "").strip()
        source = (args.get("source") or "").strip()
        if not topic or not summary:
            raise ValueError("topic and summary required")
        body = summary
        if source:
            body += f"\n\nSource: {source}"
        execute(
            """INSERT INTO journal (entry_date, title, content, mood)
               VALUES (?, ?, ?, 'research')""",
            (args.get("date") or str(date.today()),
             f"Research: {topic}", body))
        self.remember("research", f"{topic}: {summary[:100]}",
                      importance=5)
        return {"ok": True, "topic": topic}

    def _list(self, args, actor):
        rows = fetch_all(
            """SELECT id, entry_date, title, substr(content,1,200) AS excerpt
               FROM journal WHERE mood='research'
               ORDER BY entry_date DESC LIMIT 30""")
        return [dict(r) for r in rows]

    def _query(self, args, actor):
        """Answer via LLM with a source-citing prompt."""
        q = (args.get("query") or "").strip()
        if not q:
            raise ValueError("query required")
        try:
            from ...agent import Agent
            a = Agent()
            prompt = (f"Research question: {q}\n"
                      "Answer concisely and note any caveats.")
            reply = a.respond(prompt)
            return {"query": q, "answer": str(reply)[:1500]}
        except Exception as e:
            return {"query": q,
                    "error": f"{type(e).__name__}: {e}"}

    def _fetch(self, args, actor):
        """Fetch a whitelisted URL and return the first 2000 chars."""
        url = (args.get("url") or "").strip()
        if not url:
            raise ValueError("url required")
        from urllib.parse import urlparse
        host = (urlparse(url).hostname or "").lower()
        if not any(host.endswith(h) for h in self.ALLOWED_HOSTS):
            audit.log("research_fetch_denied", actor=self.NAME,
                      payload={"host": host})
            raise PermissionError(
                f"host '{host}' not in allowlist")
        try:
            import urllib.request
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mimi/10 research"})
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read(200_000).decode("utf-8", errors="replace")
            # crude text extraction
            text = re.sub(r"<script.*?</script>", " ",
                          body, flags=re.S | re.I)
            text = re.sub(r"<style.*?</style>", " ",
                          text, flags=re.S | re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return {"url": url, "excerpt": text[:2000]}
        except Exception as e:
            return {"url": url,
                    "error": f"{type(e).__name__}: {e}"}
