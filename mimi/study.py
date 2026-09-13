"""Study tracker."""
from .database import fetch_all, fetch_one, execute
from .award import award
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("NEW STUDY SESSION")
    subject = ask("Subject")
    while not subject:
        print(c("  X Subject required.", RED))
        subject = ask("Subject")
    d = ask_date("Study date")
    dur = ask_int("Duration minutes", 0, 0)
    q = ask_int("Questions solved", 0, 0)
    k = ask_int("Correct answers", 0, 0)
    if k > q:
        print(c("  X Correct > questions.", RED)); return
    notes = ask("Notes", "")
    execute("""INSERT INTO study_sessions
               (subject, study_date, duration_minutes,
                questions_solved, correct_answers, notes)
               VALUES (?, ?, ?, ?, ?, ?)""", (subject, d, dur, q, k, notes))
    acc = (k/q*100) if q else 0
    print(c("  OK Saved.", GREEN))
    print(f"  Accuracy: {acc:.1f}%")
    hours = dur / 60.0
    award("study_hour", amount=int(hours * 15))

def list_records():
    header("STUDY SESSIONS")
    rows = fetch_all("""SELECT * FROM study_sessions
                        ORDER BY study_date DESC, id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("subject","Subject"),("study_date","Date"),
                      ("duration_minutes","Minutes"),("questions_solved","Q"),
                      ("correct_answers","Correct"),("notes","Notes")])

def summary():
    r = fetch_one("""SELECT COUNT(*) AS s,
                     COALESCE(SUM(duration_minutes),0) AS m,
                     COALESCE(SUM(questions_solved),0) AS q,
                     COALESCE(SUM(correct_answers),0) AS k FROM study_sessions""")
    acc = (r["k"]/r["q"]*100) if r["q"] else 0
    print(f"\n  Sessions: {r['s']}")
    print(f"  Total: {r['m']//60}h {r['m']%60}m")
    print(f"  Accuracy: {acc:.1f}%")

def main():
    while True:
        ch = menu([("1","Add session"),("2","List"),("3","Summary"),
                   ("0","Exit")], "STUDY MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
