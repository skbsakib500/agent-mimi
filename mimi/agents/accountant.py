"""Accountant - income, expense, debt, balance."""
from datetime import date
from .base import Specialist
from ..database import fetch_one, fetch_all, execute
from ..guardian import audit


def _q(sql, params=(), default=0):
    try:
        r = fetch_one(sql, params)
        return r[0] if r else default
    except Exception:
        return default


class Accountant(Specialist):
    NAME = "accountant"
    ROLE = "accountant"
    CAPABILITIES = ("finance", "money")
    DESCRIPTION = "Income, expense, debt, cash-flow balance"

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "add_expense": self._add_expense,
            "add_income": self._add_income,
            "add_debt": self._add_debt,
            "balance": self._balance,
            "summary": self._summary,
        }
        fn = table.get(command)
        if not fn:
            raise ValueError(f"Accountant does not handle '{command}'")
        return fn(args, actor)

    def _add_txn(self, args, kind):
        try:
            amt = float(args.get("amount") or 0)
        except (TypeError, ValueError):
            raise ValueError("amount must be a number")
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
        audit.log(f"accountant_{kind}_added", actor="accountant",
                  payload={"amount": amt, "category": cat})
        return {"ok": True, "kind": kind, "amount": amt, "date": d}

    def _add_expense(self, args, actor):
        return self._add_txn(args, "expense")

    def _add_income(self, args, actor):
        return self._add_txn(args, "income")

    def _add_debt(self, args, actor):
        person = (args.get("person") or "").strip()
        if not person:
            raise ValueError("person required")
        try:
            amt = float(args.get("amount") or 0)
        except (TypeError, ValueError):
            raise ValueError("amount must be a number")
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
        audit.log("accountant_debt_added", actor="accountant",
                  payload={"person": person, "amount": amt, "type": dtype})
        return {"ok": True, "person": person, "amount": amt, "type": dtype}

    def _balance(self, args, actor):
        inc = float(_q("SELECT COALESCE(SUM(amount),0) FROM finance "
                       "WHERE transaction_type='income'"))
        exp = float(_q("SELECT COALESCE(SUM(amount),0) FROM finance "
                       "WHERE transaction_type='expense'"))
        bor = float(_q("SELECT COALESCE(SUM(amount),0) FROM finance "
                       "WHERE transaction_type='borrowed'"))
        lent = float(_q("SELECT COALESCE(SUM(amount),0) FROM finance "
                        "WHERE transaction_type='lent'"))
        return {
            "income": inc, "expense": exp,
            "borrowed": bor, "lent": lent,
            "net_earned": inc - exp,
            "cash_balance": inc + bor - exp - lent,
        }

    def _summary(self, args, actor):
        bal = self._balance(args, actor)
        active_debts = _q(
            "SELECT COUNT(*) FROM debts WHERE status='active'")
        debt_remaining = float(_q(
            "SELECT COALESCE(SUM(original_amount - paid_amount),0) FROM debts "
            "WHERE status='active'"))
        return {
            "balance": bal,
            "active_debts": int(active_debts),
            "debt_remaining": debt_remaining,
        }


accountant = Accountant()
