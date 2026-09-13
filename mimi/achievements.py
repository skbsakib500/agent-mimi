"""Achievements log."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("ACHIEVEMENTS")
    d = ask_date("Date")
    title = ask("Title")
    if not title:
        print(c("  X Title required.", RED)); return
    desc = ask("Description", "")
    cat = ask("Category", "")
    execute("""INSERT INTO achievements
               (achievement_date, title, description, category)
               VALUES (?, ?, ?, ?)""", (d, title, desc, cat))
    print(c("  OK Recorded.", GREEN))

def list_records():
    header("ACHIEVEMENTS")
    rows = fetch_all("""SELECT * FROM achievements
                        ORDER BY achievement_date DESC, id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("achievement_date","Date"),("title","Title"),
                      ("description","Description"),("category","Category")])

def delete():
    rid = ask_int("ID", minimum=1)
    if not fetch_one("SELECT id FROM achievements WHERE id=?", (rid,)):
        print(c("  X Not found.", RED)); return
    execute("DELETE FROM achievements WHERE id=?", (rid,))
    print(c("  OK Deleted.", GREEN))

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","Delete"),("0","Exit")], "ACHIEVEMENTS")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": delete()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
