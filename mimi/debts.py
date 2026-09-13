"""Debts tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import (BOLD, GREEN, RED, YELLOW, c, header, menu, ask, ask_date,
                 ask_float, ask_int, pause)

def _bal(r):
    return max(0.0, float(r["original_amount"] or 0) - float(r["paid_amount"] or 0))

def list_records():
    header("DEBTS")
    rows = fetch_all("SELECT * FROM debts ORDER BY status, id DESC")
    if not rows:
        print(c("\n  No debts.", YELLOW)); return
    total = 0.0
    for r in rows:
        b = _bal(r); total += b
        print(c(f"\n  #{r['id']} {r['person']}", BOLD))
        print(f"  Type: {r['debt_type']} | Original: {float(r['original_amount'] or 0):,.2f}")
        print(f"  Paid: {float(r['paid_amount'] or 0):,.2f} | Remaining: {b:,.2f}")
        print(f"  Status: {r['status']}")
    print(c(f"\n  Total remaining: {total:,.2f}", BOLD+GREEN))

def add():
    header("ADD DEBT")
    person = ask("Person")
    if not person:
        print(c("  X Person required.", RED)); return
    ttype = ask("Type (borrowed/lent)", "borrowed")
    amt = ask_float("Original amount", minimum=0)
    desc = ask("Description", "")
    d = ask_date("Created date")
    execute("""INSERT INTO debts (person, debt_type, original_amount,
               paid_amount, description, status, created_date)
               VALUES (?, ?, ?, 0, ?, 'active', ?)""",
            (person, ttype, amt, desc, d))
    print(c("  OK Debt saved.", GREEN))

def payment():
    header("RECORD PAYMENT")
    rid = ask_int("Debt ID", minimum=1)
    row = fetch_one("SELECT * FROM debts WHERE id=?", (rid,))
    if not row:
        print(c("  X Not found.", RED)); return
    rem = _bal(row)
    if rem <= 0:
        print(c("  Already settled.", YELLOW)); return
    amt = ask_float("Payment amount", minimum=0)
    if amt > rem:
        print(c("  X Exceeds balance.", RED)); return
    paid = float(row["paid_amount"] or 0) + amt
    status = "paid" if paid >= float(row["original_amount"] or 0) else "active"
    execute("""UPDATE debts SET paid_amount=?, status=?,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (paid, status, rid))
    print(c("  OK Payment recorded.", GREEN))

def main():
    while True:
        ch = menu([("1","List debts"),("2","Add debt"),
                   ("3","Record payment"),("0","Back")], "DEBTS MENU")
        if ch == "1": list_records(); pause()
        elif ch == "2": add(); pause()
        elif ch == "3": payment(); pause()
        elif ch == "0": break
        else:
            print(c("  X Invalid.", RED)); pause()

run = main
