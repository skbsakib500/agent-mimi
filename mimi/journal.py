"""Journal module."""
from .database import fetch_all, fetch_one, execute
from .award import award
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("NEW JOURNAL ENTRY")
    d = ask_date("Entry date")
    title = ask("Title", "")
    content = ask("Content")
    if not content:
        print(c("  X Content required.", RED)); return
    mood = ask("Mood", "")
    execute("""INSERT INTO journal (entry_date, title, content, mood)
               VALUES (?, ?, ?, ?)""", (d, title, content, mood))
    print(c("  OK Entry saved.", GREEN))
    award("journal")

def list_records():
    header("JOURNAL")
    rows = fetch_all("""SELECT * FROM journal
                        ORDER BY entry_date DESC, id DESC LIMIT 50""")
    print_rows(rows, [("id","ID"),("entry_date","Date"),("title","Title"),
                      ("content","Content"),("mood","Mood")])

def delete():
    rid = ask_int("Entry ID", minimum=1)
    if not fetch_one("SELECT id FROM journal WHERE id=?", (rid,)):
        print(c("  X Not found.", RED)); return
    execute("DELETE FROM journal WHERE id=?", (rid,))
    print(c("  OK Deleted.", GREEN))

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","Delete"),
                   ("0","Exit")], "JOURNAL MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": delete()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
