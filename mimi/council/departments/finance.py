"""Finance department - money, budget, cash flow."""
from datetime import date
from ..department import Department
from ...database import fetch_one, fetch_all, execute
from ...guardian import audit


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


class Finance(Department):
    NAME = "finance"
    ROLE = "accountant"
    MANDATE = "Track income, expense, debt, cash flow"
    CAPABILITIES = ("finance", "money", "balance",
                    "expense", "income", "debt")
    PRIORITY = 2

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "balance":       self._balance,
            "add_expense":   self._expense,
            "add_income":    self._income,
            "add_debt":      self._debt,
            "finance_summary": self._summary,
            "expense_breakdown": self._breakdown,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Finance cannot handle '{command}'")
        return fn(args, actor)

    def _balance(self, args, actor):
        inc = float(_q("SELECT COALESCE(SUM(amount),0) FROM finance "
                       "WHERE transaction_type='income'"))
        exp = float(_q("SELECT COALESCE(SUM(amount),0) FROM finance "
                       "WHERE transaction_type='expense'"))
        bor = float(_q("SELECT COALESCE(SUM(amount),0) FROM finance "
                       "WHERE transaction_type='borrowed'"))
        lent = float(_q("SELECT COALESCE(SUM(amount),0) FROM finance "
                        "WHERE transaction_type='lent'"))
        cash = inc + bor - exp - lent
        self.remember("balance_snapshot",
                      f"cash={cash:.2f}", importance=3)
        return {
            "income": inc, "expense": exp,
            "borrowed": bor, "lent": lent,
            "cash_balance": cash,
            "net_earned": inc - exp,
        }

    def _txn(self, kind, args, actor):
        try:
            amt = float(args.get("amount") or 0)
        except (TypeError, ValueError):
            raise ValueError("amount must be number")
        if amt <= 0:
            raise ValueError("amount must be > 0")
        d = args.get("date") or str(date.today())
        cat = (args.get("category") or "general").strip()
        desc = (args.get("description") or "").strip()
        execute(
            """INSERT INTO finance
               (transaction_date, transaction_type, category, amount, description)
               VALUES (?, ?, ?, ?, ?)""",
            (d, kind, cat, amt, desc))
        audit.log(f"finance_{kind}", actor=self.NAME,
                  payload={"amount": amt, "category": cat})
        self.remember("txn", f"{kind} {amt:.0f} {cat}", importance=3)
        return {"ok": True, "kind": kind, "amount": amt}

    def _expense(self, args, actor):
        return self._txn("expense", args, actor)

    def _income(self, args, actor):
        return self._txn("income", args, actor)

    def _debt(self, args, actor):
        person = (args.get("person") or "").strip()
        if not person:
            raise ValueError("person required")
        try:
            amt = float(args.get("amount") or 0)
        except (TypeError, ValueError):
            raise ValueError("amount must be number")
        if amt <= 0:
            raise ValueError("amount must be > 0")
        dtype = (args.get("type") or "borrowed").lower()
        if dtype not in ("borrowed", "lent"):
            dtype = "borrowed"
        execute(
            """INSERT INTO debts (person, debt_type, original_amount,
               paid_amount, description, status, created_date)
               VALUES (?, ?, ?, 0, ?, 'active', ?)""",
            (person, dtype, amt, args.get("description") or "",
             str(date.today())))
        audit.log("finance_debt_added", actor=self.NAME,
                  payload={"person": person, "amount": amt, "type": dtype})
        return {"ok": True, "person": person, "amount": amt, "type": dtype}

    def _summary(self, args, actor):
        bal = self._balance(args, actor)
        active = int(_q("SELECT COUNT(*) FROM debts WHERE status='active'"))
        remaining = float(_q(
            "SELECT COALESCE(SUM(original_amount - paid_amount),0) "
            "FROM debts WHERE status='active'"))
        return {
            "income": bal["income"],
            "expense": bal["expense"],
            "cash_balance": bal["cash_balance"],
            "active_debts": active,
            "debt_remaining": remaining,
        }

    def _breakdown(self, args, actor):
        rows = fetch_all(
            """SELECT category, SUM(amount) AS total, COUNT(*) AS n
               FROM finance WHERE transaction_type='expense'
               AND transaction_date >= date('now','-29 days')
               GROUP BY category ORDER BY total DESC LIMIT 10""")
        return [dict(r) for r in rows]
