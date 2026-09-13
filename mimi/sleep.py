"""Sleep tracker."""
from datetime import datetime
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, ask_time, pause, print_rows

def _dur(s, e):
    if not s or not e: return 0
    a = datetime.strptime(s, "%H:%M"); b = datetime.strptime(e, "%H:%M")
    m = int((b-a).total_seconds()/60)
    return m if m >= 0 else m + 1440

def add():
    header("SLEEP")
    d = ask_date("Sleep date")
    st = ask_time("Sleep time"); wt = ask_time("Wake time")
    m = _dur(st, wt) or ask_int("Duration minutes", 0, 0)
    q = ask_int("Quality 0-10", 0, 0, 10)
    notes = ask("Notes", "")
    execute("""INSERT INTO sleep (sleep_date, sleep_time, wake_time,
               duration_minutes, quality, notes) VALUES (?, ?, ?, ?, ?, ?)""",
            (d, st, wt, m, q, notes))
    print(c("  OK Saved.", GREEN))

def list_records():
    header("SLEEP LOGS")
    rows = fetch_all("SELECT * FROM sleep ORDER BY sleep_date DESC, id DESC LIMIT 50")
    print_rows(rows, [("id","ID"),("sleep_date","Date"),("sleep_time","Sleep"),
                      ("wake_time","Wake"),("duration_minutes","Minutes"),
                      ("quality","Quality"),("notes","Notes")])

def summary():
    r = fetch_one("""SELECT COUNT(*) AS n,
                     COALESCE(AVG(duration_minutes),0) AS m,
                     COALESCE(AVG(quality),0) AS q FROM sleep
                     WHERE sleep_date>=date('now','-6 days')""")
    print(f"\n  Nights: {r['n']}   Avg: {r['m']/60:.1f}h   Quality: {r['q']:.1f}/10")

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","7-day"),
                   ("0","Exit")], "SLEEP MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
