"""V10 Upgrade Lab - interactive approval TUI (no PIN).

Checkbox UI -> tick proposals -> confirm with 'y'.

Commands inside TUI:
  <number>  toggle that proposal (e.g. 1, or 1 3 5, or 1,3,5)
  a         tick all
  n         untick all
  y         approve selected (confirms once)
  l         refresh list
  q         quit
"""
import sys

from . import proposal
from ..guardian import audit


OWNER = "SKB Sakib"

BANNER = "+" + "-" * 68 + "+"


# ---------- state machine helper ----------

def _walk_to_approved(pid, approved_by):
    """Bring a proposal to APPROVED along a legal path."""
    p = proposal.get(pid)
    if not p:
        return False, "not found"
    status = p["status"]

    if status == "APPROVED":
        return True, "already approved"

    paths = {
        "DETECTED":         ["PROPOSED", "WAITING_APPROVAL", "APPROVED"],
        "PROPOSED":         ["WAITING_APPROVAL", "APPROVED"],
        "SANDBOX_TESTING":  ["WAITING_APPROVAL", "APPROVED"],
        "WAITING_APPROVAL": ["APPROVED"],
    }
    steps = paths.get(status)
    if steps is None:
        return False, f"cannot approve from {status}"

    for s in steps:
        ok, msg = proposal.transition(pid, s, approved_by=approved_by)
        if not ok:
            return False, f"{s}: {msg}"
    return True, "approved"


# ---------- render ----------

def _render(items, selected):
    print()
    print(BANNER)
    print("|  *  UPGRADE APPROVAL                                            |")
    print(f"|  Owner: {OWNER:<56}|")
    print(BANNER)
    for i, p in enumerate(items, 1):
        mark = "[x]" if p["id"] in selected else "[ ]"
        print(f"  {mark} {i:>2}) #{p['id']:<4} "
              f"[{p['status']:<16}] {p['category']:<8}/{p['module']}")
        problem = (p.get("problem") or "")[:62]
        print(f"          {problem}")
    print("-" * 70)
    print(f"  selected: {len(selected)}/{len(items)}")
    print("  <num>=toggle  a=all  n=none  y=approve  l=refresh  q=quit")
    print()


# ---------- actions ----------

def _approve(selected_ids, items):
    print()
    print(f"  Approving {len(selected_ids)} proposal(s):")
    for p in items:
        if p["id"] in selected_ids:
            print(f"    #{p['id']:<4} {p['category']}/{p['module']}  "
                  f"{(p.get('problem') or '')[:50]}")

    audit.log("approve_batch", actor="tui",
              payload={"count": len(selected_ids),
                       "ids": sorted(selected_ids)})

    ok_list, fail_list = [], []
    for pid in sorted(selected_ids):
        ok, msg = _walk_to_approved(pid, approved_by=OWNER)
        if ok:
            ok_list.append(pid)
            print(f"    #{pid}: APPROVED")
        else:
            fail_list.append((pid, msg))
            print(f"    #{pid}: FAILED - {msg}")

    print()
    print(f"  result: {len(ok_list)} approved, {len(fail_list)} failed")


# ---------- TUI loop ----------

def cmd_tui():
    items = proposal.pending()
    if not items:
        print("  no pending proposals")
        return 0

    selected = set()
    while True:
        _render(items, selected)
        try:
            raw = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not raw:
            continue
        if raw in ("q", "quit", "exit"):
            return 0
        if raw == "a":
            selected = {p["id"] for p in items}
            continue
        if raw == "n":
            selected = set()
            continue
        if raw == "l":
            items = proposal.pending()
            selected &= {p["id"] for p in items}
            continue
        if raw == "y":
            if not selected:
                print("  nothing selected")
                continue
            _approve(selected, items)
            items = proposal.pending()
            selected = set()
            if not items:
                print("  all pending cleared. bye.")
                return 0
            continue

        # numeric toggle
        parts = raw.replace(",", " ").split()
        toggled = False
        for tok in parts:
            try:
                n = int(tok)
            except ValueError:
                print(f"  unknown: {tok}")
                continue
            if 1 <= n <= len(items):
                pid = items[n - 1]["id"]
                if pid in selected:
                    selected.discard(pid)
                else:
                    selected.add(pid)
                toggled = True
            else:
                print(f"  pick 1..{len(items)}")
        if not toggled:
            continue


def cmd_list():
    for p in proposal.pending():
        print(f"  #{p['id']:<4} [{p['status']:<16}] "
              f"{p['category']:<8}/{p['module']:<12} "
              f"{(p.get('problem') or '')[:50]}")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tui"
    if cmd == "tui":
        return cmd_tui()
    if cmd == "list":
        return cmd_list()
    print("usage: python -m mimi.upgrade.approve_tui [tui|list]")
    return 1


if __name__ == "__main__":
    sys.exit(main())
