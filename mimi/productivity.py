"""Productivity tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("PRODUCTIVITY")
    d = ask_date()
    prod = ask_int("Productive minutes", 0, 0)
    waste = ask_int("Wasted minutes", 0, 0)
    total = prod + waste
    score = round(prod/total*100) if total else 0
    notes = ask("Notes", "")
    execute("""INSERT INTO productivity (log_date, productive_minutes,
               wasted_minutes, score, notes) VALUES (?, ?, ?, ?, ?)""",
            (d, prod, waste, score, notes))
    print(c(f"  OK Saved. Score: {score}/100", GREEN))

def list_records():
    header("PRODUCTIVITY")
    rows = fetch_all("""SELECT * FROM productivity
                        ORDER BY log_date DESC, id DESC LIMIT 50""")
    print_rows(rows, [("id","ID"),("log_date","Date"),
                      ("productive_minutes","Prod min"),
                      ("wasted_minutes","Waste min"),("score","Score"),
                      ("notes","Notes")])

def summary():
    r = fetch_one("""SELECT COUNT(*) AS d,
                     COALESCE(SUM(productive_minutes),0) AS p,
                     COALESCE(SUM(wasted_minutes),0) AS w,
                     ROUND(AVG(score),1) AS s FROM productivity
                     WHERE log_date>=date('now','-6 days')""")
    print(f"\n  Days: {r['d']}   Productive: {r['p']}min   "
          f"Wasted: {r['w']}min   Avg: {r['s'] or 0}/100")

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","Summary"),
                   ("0","Exit")], "PRODUCTIVITY MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
