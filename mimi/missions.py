"""Missions module."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("NEW MISSION")
    title = ask("Title")
    if not title:
        print(c("  X Title required.", RED)); return
    goal_id = ask_int("Goal ID (0 = none)", 0, 0)
    desc = ask("Description", "")
    deadline = ask_date("Deadline", allow_blank=True)
    priority = ask("Priority", "medium")
    progress = ask_int("Progress %", 0, 0, 100)
    status = "completed" if progress == 100 else "active"
    execute("""INSERT INTO missions (goal_id, title, description, deadline,
               priority, progress, status) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (goal_id or None, title, desc, deadline, priority, progress, status))
    print(c("  OK Mission saved.", GREEN))

def list_records():
    header("MISSIONS")
    rows = fetch_all("""SELECT m.*, g.title AS goal_title FROM missions m
                        LEFT JOIN goals g ON m.goal_id=g.id
                        ORDER BY CASE m.priority WHEN 'critical' THEN 1
                                 WHEN 'high' THEN 2 WHEN 'medium' THEN 3
                                 ELSE 4 END, m.id DESC""")
    print_rows(rows, [("id","ID"),("title","Title"),("goal_title","Goal"),
                      ("deadline","Deadline"),("priority","Priority"),
                      ("progress","Progress %"),("status","Status")])

def sync_progress(mission_id):
    r = fetch_one("""SELECT COUNT(*) AS total,
        COALESCE(SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END),0) AS done
        FROM tasks WHERE mission_id=?""", (mission_id,))
    if r["total"]:
        p = round(100 * r["done"] / r["total"])
        s = "completed" if p == 100 else "active"
        execute("UPDATE missions SET progress=?, status=? WHERE id=?",
                (p, s, mission_id))

def summary():
    r = fetch_one("""SELECT COUNT(*) AS t,
        SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done,
        COALESCE(AVG(progress),0) AS avg FROM missions""")
    print(f"\n  Total: {r['t']}   Done: {r['done'] or 0}   Avg: {r['avg']:.1f}%")

def main():
    while True:
        ch = menu([("1","Add mission"),("2","List"),("3","Summary"),
                   ("0","Exit")], "MISSIONS MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
