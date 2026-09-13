"""Routine/habit tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("ROUTINES")
    d = ask_date("Routine date")
    habit = ask("Habit")
    if not habit:
        print(c("  X Habit required.", RED)); return
    done = ask_int("Completed? 1=yes, 0=no", 0, 0, 1)
    notes = ask("Notes", "")
    execute("""INSERT INTO routines (routine_date, habit, completed, notes)
               VALUES (?, ?, ?, ?)""", (d, habit, done, notes))
    print(c("  OK Saved.", GREEN))

def list_records():
    header("ROUTINES")
    rows = fetch_all("""SELECT * FROM routines
                        ORDER BY routine_date DESC, id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("routine_date","Date"),("habit","Habit"),
                      ("completed","Done"),("notes","Notes")])

def summary():
    r = fetch_one("""SELECT COUNT(*) AS t,
                     COALESCE(SUM(completed),0) AS d,
                     ROUND(CASE WHEN COUNT(*)
                           THEN 100.0*SUM(completed)/COUNT(*)
                           ELSE 0 END, 1) AS r FROM routines
                     WHERE routine_date>=date('now','-6 days')""")
    print(f"\n  Records: {r['t']}   Done: {r['d']}   Rate: {r['r']}%")

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","7-day"),
                   ("0","Exit")], "ROUTINES MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
