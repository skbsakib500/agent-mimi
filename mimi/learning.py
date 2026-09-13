"""Learning tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("LEARNING")
    d = ask_date("Date")
    topic = ask("Topic")
    if not topic:
        print(c("  X Topic required.", RED)); return
    src = ask("Source", "")
    mins = ask_int("Duration minutes", 0, 0)
    notes = ask("Notes", "")
    execute("""INSERT INTO learning (learning_date, topic, source,
               duration_minutes, notes) VALUES (?, ?, ?, ?, ?)""",
            (d, topic, src, mins, notes))
    print(c("  OK Saved.", GREEN))

def list_records():
    header("LEARNING LOG")
    rows = fetch_all("""SELECT * FROM learning
                        ORDER BY learning_date DESC, id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("learning_date","Date"),("topic","Topic"),
                      ("source","Source"),("duration_minutes","Minutes"),
                      ("notes","Notes")])

def summary():
    r = fetch_one("""SELECT COUNT(*) AS n, COALESCE(SUM(duration_minutes),0) AS m
                     FROM learning WHERE learning_date>=date('now','-6 days')""")
    print(f"\n  Entries: {r['n']}   Time: {r['m']} min ({r['m']/60:.1f}h)")

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","7-day"),("0","Exit")], "LEARNING")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
