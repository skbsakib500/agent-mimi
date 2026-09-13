"""Finance tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import (BOLD, GREEN, RED, YELLOW, c, clear, header, menu, ask,
                 ask_date, ask_float, pause, section)

TYPES = {"1":("income","Income"),"2":("expense","Expense"),
         "3":("borrowed","Borrowed"),"4":("lent","Lent")}

def add():
    clear(); header("ADD TRANSACTION")
    for k, (_, l) in TYPES.items():
        print(f"  {k}. {l}")
    ch = input(c("\n  Type: ", BOLD)).strip()
    if ch not in TYPES:
        print(c("  X Invalid.", RED)); pause(); return
    ttype, label = TYPES[ch]
    d = ask_date("Date")
    amt = ask_float("Amount", minimum=0.01)
    cat = ask("Category", "")
    desc = ask("Description", "")
    execute("""INSERT INTO finance (transaction_date, transaction_type,
               category, amount, description) VALUES (?, ?, ?, ?, ?)""",
            (d, ttype, cat, amt, desc))
    print(c(f"  OK {label} saved.", GREEN))
    pause()

def list_records():
    header("TRANSACTIONS")
    rows = fetch_all("""SELECT * FROM finance
                        ORDER BY transaction_date DESC, id DESC LIMIT 100""")
    if not rows:
        print(c("\n  No transactions.", YELLOW)); pause(); return
    for r in rows:
        st = GREEN if r["transaction_type"]=="income" else \
             RED if r["transaction_type"]=="expense" else YELLOW
        print(f"  #{r['id']} {r['transaction_date']} "
              f"{c(r['transaction_type'].upper(), st)} {r['amount']:.2f}")
        print(f"      {r['category'] or '-'} | {r['description'] or '-'}")
    pause()

def summary():
    rows = fetch_all("""SELECT transaction_type,
                        COALESCE(SUM(amount),0) AS total
                        FROM finance GROUP BY transaction_type""")
    t = {r["transaction_type"]: float(r["total"]) for r in rows}
    inc, exp = t.get("income",0), t.get("expense",0)
    bor, lent = t.get("borrowed",0), t.get("lent",0)
    cash = inc + bor - exp - lent
    clear(); header("FINANCIAL SUMMARY")
    section("CASH FLOW", "[$]")
    print(f"  Income   : {c(f'{inc:,.2f}', GREEN)}")
    print(f"  Expense  : {c(f'{exp:,.2f}', RED)}")
    print(f"  Borrowed : {c(f'{bor:,.2f}', YELLOW)}")
    print(f"  Lent     : {c(f'{lent:,.2f}', YELLOW)}")
    section("POSITION", "[=]")
    col = GREEN if cash >= 0 else RED
    print(f"  Cash Balance: {c(f'{cash:,.2f}', BOLD+col)}")
    pause()

def dashboard():
    r = fetch_one("""SELECT
        COALESCE(SUM(CASE WHEN transaction_type='income'   THEN amount ELSE 0 END),0) inc,
        COALESCE(SUM(CASE WHEN transaction_type='expense'  THEN amount ELSE 0 END),0) exp,
        COALESCE(SUM(CASE WHEN transaction_type='borrowed' THEN amount ELSE 0 END),0) bor,
        COALESCE(SUM(CASE WHEN transaction_type='lent'     THEN amount ELSE 0 END),0) lent,
        COUNT(*) AS cnt FROM finance""")
    cash = r["inc"] + r["bor"] - r["exp"] - r["lent"]
    clear(); header("FINANCE")
    section("SNAPSHOT", "[!]")
    print(f"  Income   {r['inc']:,.2f}")
    print(f"  Expense  {r['exp']:,.2f}")
    print(f"  Cash     {c(f'{cash:,.2f}', GREEN if cash>=0 else RED)}")
    print(f"  Records  {r['cnt']}")

def main():
    while True:
        dashboard(); print()
        print("  1. Add transaction")
        print("  2. List")
        print("  3. Summary")
        print("  0. Back")
        ch = input(c("\n  > Select: ", BOLD)).strip()
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": summary()
        elif ch == "0": break
        else:
            print(c("  X Invalid.", RED)); pause()

run = main
