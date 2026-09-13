"""Career/application tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("CAREER")
    org = ask("Organization")
    pos = ask("Position")
    if not org or not pos:
        print(c("  X Org and position required.", RED)); return
    ad = ask_date("Application date", allow_blank=True)
    ed = ask_date("Exam date", allow_blank=True)
    st = ask("Status", "applied")
    pg = ask_int("Prep progress %", 0, 0, 100)
    notes = ask("Notes", "")
    execute("""INSERT INTO career (organization, position, application_date,
               exam_date, status, preparation_progress, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (org, pos, ad, ed, st, pg, notes))
    print(c("  OK Saved.", GREEN))

def list_records():
    header("CAREER LOG")
    rows = fetch_all("""SELECT * FROM career ORDER BY id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("organization","Org"),("position","Position"),
                      ("application_date","Applied"),("exam_date","Exam"),
                      ("status","Status"),("preparation_progress","Prep %"),
                      ("notes","Notes")])

def summary():
    r = fetch_one("""SELECT COUNT(*) AS t,
                     COALESCE(AVG(preparation_progress),0) AS a
                     FROM career""")
    print(f"\n  Applications: {r['t']}   Avg prep: {r['a']:.1f}%")

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","Summary"),("0","Exit")], "CAREER")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
