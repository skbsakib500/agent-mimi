"""Mistakes / lessons tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("MISTAKES")
    d = ask_date("Date")
    title = ask("Title")
    if not title:
        print(c("  X Title required.", RED)); return
    what = ask("What happened", "")
    reason = ask("Reason", "")
    lesson = ask("Lesson", "")
    action = ask("Action plan", "")
    execute("""INSERT INTO mistakes
               (mistake_date, title, what_happened, reason, lesson, action_plan)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (d, title, what, reason, lesson, action))
    print(c("  OK Recorded.", GREEN))

def list_records():
    header("MISTAKE LOG")
    rows = fetch_all("""SELECT * FROM mistakes
                        ORDER BY mistake_date DESC, id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("mistake_date","Date"),("title","Title"),
                      ("reason","Reason"),("lesson","Lesson"),
                      ("action_plan","Action")])

def update():
    rid = ask_int("ID", minimum=1)
    row = fetch_one("SELECT * FROM mistakes WHERE id=?", (rid,))
    if not row:
        print(c("  X Not found.", RED)); return
    execute("""UPDATE mistakes SET mistake_date=?, title=?, what_happened=?,
               reason=?, lesson=?, action_plan=? WHERE id=?""",
            (ask_date("Date", row["mistake_date"]),
             ask("Title", row["title"]),
             ask("What", row["what_happened"] or ""),
             ask("Reason", row["reason"] or ""),
             ask("Lesson", row["lesson"] or ""),
             ask("Action", row["action_plan"] or ""), rid))
    print(c("  OK Updated.", GREEN))

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","Update"),("0","Exit")], "MISTAKES")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": update()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
