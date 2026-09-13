"""Faith tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("FAITH")
    d = ask_date("Date")
    act = ask("Activity")
    if not act:
        print(c("  X Activity required.", RED)); return
    done = ask_int("Completed? 1/0", 0, 0, 1)
    notes = ask("Notes", "")
    execute("""INSERT INTO faith (faith_date, activity, completed, notes)
               VALUES (?, ?, ?, ?)""", (d, act, done, notes))
    print(c("  OK Saved.", GREEN))

def list_records():
    header("FAITH LOG")
    rows = fetch_all("""SELECT * FROM faith ORDER BY faith_date DESC, id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("faith_date","Date"),("activity","Activity"),
                      ("completed","Done"),("notes","Notes")])

def summary():
    r = fetch_one("""SELECT COUNT(*) AS t, COALESCE(SUM(completed),0) AS d
                     FROM faith WHERE faith_date>=date('now','-6 days')""")
    print(f"\n  Activities: {r['t']}   Completed: {r['d']}")

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","7-day"),("0","Exit")], "FAITH")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
