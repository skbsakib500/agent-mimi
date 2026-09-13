"""Tasks module."""
from datetime import datetime
from .database import fetch_all, fetch_one, execute
from .award import award
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("NEW TASK")
    title = ask("Title")
    if not title:
        print(c("  X Title required.", RED)); return
    mid = ask_int("Mission ID (0 = none)", 0, 0)
    desc = ask("Description", "")
    due = ask_date("Due date", allow_blank=True)
    priority = ask("Priority", "medium")
    execute("""INSERT INTO tasks (mission_id, title, description, due_date,
               priority, status) VALUES (?, ?, ?, ?, ?, 'pending')""",
            (mid or None, title, desc, due, priority))
    print(c("  OK Task saved.", GREEN))

def list_records():
    header("TASKS")
    rows = fetch_all("""SELECT t.*, m.title AS mission_title FROM tasks t
                        LEFT JOIN missions m ON t.mission_id=m.id
                        ORDER BY COALESCE(t.due_date,'9999-12-31'),
                        t.id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("mission_title","Mission"),("title","Task"),
                      ("due_date","Due"),("priority","Priority"),
                      ("status","Status"),("completed_at","Done at")])

def complete():
    header("COMPLETE TASK")
    rid = ask_int("Task ID", minimum=1)
    row = fetch_one("SELECT * FROM tasks WHERE id=?", (rid,))
    if not row:
        print(c("  X Not found.", RED)); return
    now = datetime.now().isoformat(timespec="seconds")
    execute("UPDATE tasks SET status='completed', completed_at=? WHERE id=?",
            (now, rid))
    if row["mission_id"]:
        from .missions import sync_progress
        sync_progress(row["mission_id"])
    print(c("  OK Task completed.", GREEN))
    award("task_complete")

def summary():
    r = fetch_one("""SELECT COUNT(*) AS t,
        SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done,
        SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pend FROM tasks""")
    print(f"\n  Total: {r['t']}   Done: {r['done'] or 0}   Pending: {r['pend'] or 0}")

def main():
    while True:
        ch = menu([("1","Add task"),("2","List"),("3","Complete"),
                   ("4","Summary"),("0","Exit")], "TASKS MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": complete()
        elif ch == "4": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
