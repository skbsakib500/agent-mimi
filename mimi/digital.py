"""Digital usage tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("DIGITAL USAGE")
    d = ask_date("Date")
    app = ask("App")
    cat = ask("Category", "social")
    mins = ask_int("Minutes", 0, 0)
    notes = ask("Notes", "")
    execute("""INSERT INTO digital_usage
               (usage_date, app_name, category, duration_minutes, notes)
               VALUES (?, ?, ?, ?, ?)""", (d, app, cat, mins, notes))
    print(c("  OK Saved.", GREEN))

def list_records():
    header("DIGITAL LOG")
    rows = fetch_all("""SELECT * FROM digital_usage
                        ORDER BY usage_date DESC, id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("usage_date","Date"),("app_name","App"),
                      ("category","Category"),("duration_minutes","Minutes")])

def summary():
    r = fetch_one("""SELECT COALESCE(SUM(duration_minutes),0) AS m,
                     COUNT(*) AS n FROM digital_usage
                     WHERE usage_date>=date('now','-6 days')""")
    print(f"\n  7-day usage: {r['m']} min ({r['m']/60:.1f}h)   Entries: {r['n']}")

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","7-day"),("0","Exit")], "DIGITAL")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
