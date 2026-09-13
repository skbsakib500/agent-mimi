"""Time tracking."""
from datetime import datetime
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, ask_time, pause, print_rows

def _dur(s, e):
    if not s or not e: return 0
    a = datetime.strptime(s, "%H:%M"); b = datetime.strptime(e, "%H:%M")
    m = int((b-a).total_seconds()/60)
    return m if m >= 0 else m + 1440

def add():
    header("TIME TRACKING")
    d = ask_date()
    cat = ask("Category")
    if not cat:
        print(c("  X Category required.", RED)); return
    s = ask_time("Start"); e = ask_time("End")
    dur = _dur(s, e) or ask_int("Duration minutes", 0, 0)
    notes = ask("Notes", "")
    execute("""INSERT INTO time_logs (log_date, category, start_time,
               end_time, duration_minutes, notes) VALUES (?, ?, ?, ?, ?, ?)""",
            (d, cat, s, e, dur, notes))
    print(c("  OK Saved.", GREEN))

def list_records():
    header("TIME LOGS")
    rows = fetch_all("""SELECT * FROM time_logs
                        ORDER BY log_date DESC, id DESC LIMIT 50""")
    print_rows(rows, [("id","ID"),("log_date","Date"),("category","Category"),
                      ("start_time","Start"),("end_time","End"),
                      ("duration_minutes","Minutes"),("notes","Notes")])

def summary():
    r = fetch_one("""SELECT COALESCE(SUM(duration_minutes),0) AS m,
                     COUNT(*) AS c FROM time_logs
                     WHERE log_date>=date('now','-6 days')""")
    print(f"\n  7-day: {r['m']} min ({r['m']/60:.1f}h)   Entries: {r['c']}")

def main():
    while True:
        ch = menu([("1","Add log"),("2","List"),("3","7-day"),
                   ("0","Exit")], "TIME MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
