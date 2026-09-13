"""Goals module."""
from .database import fetch_all, fetch_one, execute
from .award import award
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("NEW GOAL")
    title = ask("Title")
    if not title:
        print(c("  X Title required.", RED)); return
    desc = ask("Description", "")
    deadline = ask_date("Deadline", allow_blank=True)
    priority = ask("Priority (low/medium/high/critical)", "medium")
    progress = ask_int("Progress %", 0, 0, 100)
    status = "completed" if progress == 100 else "active"
    execute("""INSERT INTO goals (title, description, deadline, priority, progress, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, desc, deadline, priority, progress, status))
    print(c("  OK Goal saved.", GREEN))
    award("goal_done", amount=10)

def list_records():
    header("GOALS")
    rows = fetch_all("""SELECT * FROM goals ORDER BY
        CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                      WHEN 'medium' THEN 3 ELSE 4 END, id DESC""")
    print_rows(rows, [("id","ID"),("title","Title"),("deadline","Deadline"),
                      ("priority","Priority"),("progress","Progress %"),
                      ("status","Status")])

def update():
    rid = ask_int("Goal ID", minimum=1)
    row = fetch_one("SELECT * FROM goals WHERE id=?", (rid,))
    if not row:
        print(c("  X Not found.", RED)); return
    progress = ask_int("Progress %", row["progress"], 0, 100)
    status = "completed" if progress == 100 else "active"
    execute("""UPDATE goals SET title=?, description=?, deadline=?, priority=?,
               progress=?, status=? WHERE id=?""",
            (ask("Title", row["title"]),
             ask("Description", row["description"] or ""),
             ask_date("Deadline", row["deadline"], allow_blank=True),
             ask("Priority", row["priority"]), progress, status, rid))
    print(c("  OK Updated.", GREEN))
    if progress == 100 and (row["progress"] or 0) < 100:
        award("goal_done")

def summary():
    r = fetch_one("""SELECT COUNT(*) AS t,
        SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done,
        COALESCE(AVG(progress),0) AS avg FROM goals""")
    print(f"\n  Total: {r['t']}   Done: {r['done'] or 0}   Avg: {r['avg']:.1f}%")

def main():
    while True:
        ch = menu([("1","Add goal"),("2","List"),("3","Update"),
                   ("4","Summary"),("0","Exit")], "GOALS MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": update()
        elif ch == "4": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
