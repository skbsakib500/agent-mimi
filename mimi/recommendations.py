"""Agent Mimi - persistence of recommendations (bug-fixed V10.8 lesson)."""
from .database import execute, fetch_all


def save(rule):
    exists = fetch_all(
        """SELECT id FROM recommendations
           WHERE title=? AND message=? AND date(created_at)=date('now')
           LIMIT 1""",
        (rule.title, rule.message))
    if exists:
        return False
    execute("""INSERT INTO recommendations
               (category, priority, title, message, source_module, is_read)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (rule.module, rule.severity, rule.title, rule.message, "automation"))
    execute("""INSERT INTO intelligence_logs
               (event_type, severity, title, message, module)
               VALUES ('automation', ?, ?, ?, ?)""",
            (rule.severity, rule.title, rule.message, rule.module))
    return True


def save_all(rules):
    return sum(save(r) for r in rules)


def recent(limit=20):
    return fetch_all("""SELECT * FROM recommendations
                        ORDER BY id DESC LIMIT ?""", (limit,))
