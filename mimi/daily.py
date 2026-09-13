"""Daily life log."""
from datetime import date
from .database import fetch_all, fetch_one, execute
from .award import award
from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, c, header, menu, ask,
                 ask_date, ask_float, ask_int, ask_time, pause)

def add():
    header("NEW DAILY ENTRY")
    d = ask_date("Date")
    wake = ask_time("Wake time", allow_blank=True) or ""
    sleep = ask_time("Sleep time", allow_blank=True) or ""
    study = ask_float("Study hours", 0.0, 0)
    prod = ask_float("Productive hours", 0.0, 0)
    waste = ask_float("Wasted hours", 0.0, 0)
    exer = ask_int("Exercise minutes", 0, 0)
    phone = ask_int("Phone usage minutes", 0, 0)
    inc = ask_float("Income", 0.0, 0)
    exp = ask_float("Expense", 0.0, 0)
    energy = ask_int("Energy (1-10)", 5, 1, 10)
    event = ask("Important event", "")
    j = ask("Journal", "")
    execute("""INSERT OR REPLACE INTO daily_logs
               (log_date, wake_time, sleep_time, study_hours,
                productive_hours, wasted_hours, exercise_minutes,
                phone_usage_minutes, income, expense, energy,
                important_event, journal, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (d, wake, sleep, study, prod, waste, exer, phone,
             inc, exp, energy, event, j))
    print(c("  OK Daily log saved.", GREEN))
    award("daily_log")

def list_records():
    header("DAILY LOGS")
    rows = fetch_all("SELECT * FROM daily_logs ORDER BY log_date DESC LIMIT 100")
    if not rows:
        print(c("\n  No logs.", DIM+WHITE)); return
    for r in rows:
        print(c(f"\n  {r['log_date']}", BOLD+CYAN))
        print(f"  Study {r['study_hours']}h  "
              f"Productive {r['productive_hours']}h  "
              f"Wasted {r['wasted_hours']}h")
        print(f"  Exercise {r['exercise_minutes']}min  "
              f"Phone {r['phone_usage_minutes']}min  "
              f"Energy {r['energy']}/10")

def summary():
    today = str(date.today())
    r = fetch_one("SELECT * FROM daily_logs WHERE log_date=?", (today,))
    header("TODAY SUMMARY")
    if not r:
        print(c(f"  No entry for {today}.", RED)); return
    print(f"  Study: {r['study_hours']}h   Productive: {r['productive_hours']}h")
    print(f"  Exercise: {r['exercise_minutes']}min   Phone: {r['phone_usage_minutes']}min")
    print(f"  Income: {r['income']}   Expense: {r['expense']}")
    print(f"  Energy: {r['energy']}/10")

def main():
    while True:
        ch = menu([("1","Add entry"),("2","List"),("3","Today"),
                   ("0","Exit")], "DAILY MENU")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
