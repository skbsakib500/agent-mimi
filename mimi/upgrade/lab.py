"""V10 Upgrade Lab - unified menu.

Ties together: detect -> propose -> sandbox -> approve -> apply -> verify
                                                    \-> rollback
"""
from . import proposal, detect, sandbox, apply as apply_mod
from ..guardian import audit
from ..guardian.permissions import check


# ──────────────── programmatic API ────────────────

def run_full_cycle(actor="SKB Sakib", approved_by=None, auto_apply=False):
    """End-to-end safe pipeline.

    detect -> propose -> sandbox test -> (optionally) apply if owner approves.
    Returns a summary dict. Never raises.
    """
    summary = {"steps": [], "proposals": [], "applied": [],
               "rolled_back": [], "errors": []}

    # 1. Detect
    try:
        findings = detect.scan()
        summary["steps"].append({"step": "detect", "ok": True,
                                  "findings": len(findings)})
    except Exception as e:
        summary["errors"].append(f"detect: {type(e).__name__}: {e}")
        summary["steps"].append({"step": "detect", "ok": False})
        return summary

    # 2. Propose
    try:
        new_ids = detect.to_proposals(findings)
        summary["steps"].append({"step": "propose", "ok": True,
                                  "created": len(new_ids)})
    except Exception as e:
        summary["errors"].append(f"propose: {type(e).__name__}: {e}")
        summary["steps"].append({"step": "propose", "ok": False})
        return summary

    # 3. Sandbox test pending proposals
    for p in proposal.pending():
        pid = p["id"]
        if p["status"] not in ("PROPOSED", "DETECTED"):
            continue
        try:
            proposal.transition(pid, "SANDBOX_TESTING", actor="lab")
            r = sandbox.run_tests(pid)
            sandbox.cleanup(pid)
            if r["pass"]:
                proposal.transition(
                    pid, "WAITING_APPROVAL",
                    note="sandbox passed",
                    extra={"sandbox_result": {
                        "imports_ok": r["imports"]["ok"],
                        "tests_ran": r["tests"]["ran"],
                        "tests_failed": r["tests"]["failed"],
                        "elapsed": r["elapsed_sec"],
                    }},
                    actor="lab")
                summary["proposals"].append({"id": pid, "stage": "tested"})
            else:
                proposal.transition(pid, "FAILED",
                                    note="sandbox failed",
                                    actor="lab")
                summary["proposals"].append({"id": pid,
                                              "stage": "sandbox_failed"})
        except Exception as e:
            summary["errors"].append(
                f"sandbox pid={pid}: {type(e).__name__}: {e}")

    summary["steps"].append({"step": "sandbox", "ok": True})

    # 4. Optional apply
    if auto_apply and approved_by == "SKB Sakib":
        for p in proposal.list_by_status("WAITING_APPROVAL"):
            pid = p["id"]
            try:
                proposal.transition(pid, "APPROVED", actor=actor,
                                    approved_by=approved_by)
                proposal.transition(pid, "APPLYING", actor=actor,
                                    approved_by=approved_by)
                # In absence of a real candidate sandbox, this is a no-op
                # apply: we re-verify current production.
                v = apply_mod.verify(actor=actor)
                if v["passed"]:
                    proposal.transition(
                        pid, "VERIFIED",
                        note="verify passed (no-op apply)",
                        extra={"verify_result": {
                            "imports_ok": v["imports_ok"],
                            "imports_broken": len(v["imports_broken"]),
                            "health_issues": len(v["health_issues"]),
                        }},
                        actor=actor, approved_by=approved_by)
                    summary["applied"].append(pid)
                else:
                    proposal.transition(pid, "FAILED",
                                        note="verify failed",
                                        actor=actor)
                    proposal.transition(pid, "ROLLED_BACK",
                                        note="nothing to rollback (no-op apply)",
                                        actor=actor, approved_by=approved_by)
                    summary["rolled_back"].append(pid)
            except Exception as e:
                summary["errors"].append(
                    f"apply pid={pid}: {type(e).__name__}: {e}")

    summary["steps"].append({"step": "complete", "ok": True})
    audit.log("lab_cycle", actor=actor,
              payload={"steps": len(summary["steps"]),
                       "applied": len(summary["applied"]),
                       "rolled_back": len(summary["rolled_back"]),
                       "errors": len(summary["errors"])})
    return summary


# ──────────────── TUI menu ────────────────

def _print_summary(s):
    from ..ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from ..ui import c
    print()
    for st in s["steps"]:
        mark = c("OK", GREEN) if st["ok"] else c("X", RED)
        extras = ""
        for k in ("findings", "created"):
            if k in st:
                extras += f"  {k}={st[k]}"
        print(f"  [{mark}] {st['step']}{extras}")
    if s["proposals"]:
        print(f"  tested proposals: {len(s['proposals'])}")
    if s["applied"]:
        print(c(f"  applied: {s['applied']}", GREEN))
    if s["rolled_back"]:
        print(c(f"  rolled back: {s['rolled_back']}", YELLOW))
    for e in s["errors"]:
        print(c(f"  ! {e}", RED))


def _list_pending():
    from ..ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from ..ui import c, clear, header
    clear()
    header("📬 PENDING PROPOSALS", "Upgrade Lab")
    rows = proposal.pending()
    if not rows:
        print(c("\n  (none)", DIM + WHITE))
        return
    for p in rows:
        risk = p["risk_level"] or "low"
        col = RED if risk == "critical" else YELLOW if risk in ("high", "medium") else GREEN
        print(f"\n  #{p['id']:<4} {c(p['status'], CYAN)}  "
              f"{c(risk, col)}  {p['category']}/{p['module']}")
        if p["problem"]:
            print(f"        problem : {p['problem'][:70]}")
        if p["proposal"]:
            print(f"        action  : {p['proposal'][:70]}")


def _sandbox_one():
    from ..ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from ..ui import c, clear, header, pause
    clear()
    header("🧪 SANDBOX TEST", "Pick a proposal")
    _list_pending()
    pid = input(c("\n  Proposal # (blank=cancel): ", BOLD)).strip()
    if not pid.isdigit():
        return
    pid = int(pid)
    p = proposal.get(pid)
    if not p:
        print(c("  X not found", RED)); pause(); return
    if p["status"] not in ("PROPOSED", "DETECTED"):
        print(c(f"  X cannot test from {p['status']}", RED)); pause(); return
    proposal.transition(pid, "SANDBOX_TESTING")
    print(c(f"  running sandbox for #{pid}...", DIM + WHITE))
    r = sandbox.run_tests(pid)
    sandbox.cleanup(pid)
    print()
    print(f"  pass         : {r['pass']}")
    print(f"  imports ok   : {r['imports']['ok']}")
    print(f"  imports fail : {len(r['imports']['broken'])}")
    print(f"  tests ran    : {r['tests']['ran']}")
    print(f"  tests failed : {r['tests']['failed']}")
    print(f"  elapsed      : {r['elapsed_sec']}s")
    if r["pass"]:
        proposal.transition(pid, "WAITING_APPROVAL",
                            note="sandbox passed",
                            extra={"sandbox_result": {
                                "imports_ok": r["imports"]["ok"],
                                "tests_ran": r["tests"]["ran"],
                                "tests_failed": r["tests"]["failed"],
                                "elapsed": r["elapsed_sec"],
                            }})
        print(c(f"  -> WAITING_APPROVAL", GREEN))
    else:
        proposal.transition(pid, "FAILED", note="sandbox failed")
        print(c(f"  -> FAILED", RED))
    pause()


def _approve_one():
    from ..ui import (BOLD, GREEN, RED, YELLOW)
    from ..ui import c, clear, header, pause
    clear()
    header("✅ APPROVE PROPOSAL", "Owner: SKB Sakib")
    rows = proposal.list_by_status("WAITING_APPROVAL")
    if not rows:
        print(c("\n  (nothing waiting approval)", YELLOW)); pause(); return
    for p in rows:
        print(f"\n  #{p['id']:<4} {p['category']}/{p['module']}")
        print(f"        problem : {(p['problem'] or '')[:70]}")
        print(f"        action  : {(p['proposal'] or '')[:70]}")
    pid = input(c("\n  Proposal #: ", BOLD)).strip()
    if not pid.isdigit():
        return
    pid = int(pid)
    confirm = input(c(f"  Type 'APPROVE {pid}' to confirm: ", BOLD + YELLOW)).strip()
    if confirm != f"APPROVE {pid}":
        print(c("  cancelled.", RED)); pause(); return
    ok, msg = proposal.transition(pid, "APPROVED", actor="SKB Sakib",
                                   approved_by="SKB Sakib")
    if not ok:
        print(c(f"  X {msg}", RED)); pause(); return
    print(c(f"  OK {msg}", GREEN))

    # apply
    ok, msg = proposal.transition(pid, "APPLYING", actor="SKB Sakib",
                                   approved_by="SKB Sakib")
    print(f"  {msg}")
    v = apply_mod.verify(actor="SKB Sakib")
    if v["passed"]:
        proposal.transition(pid, "VERIFIED",
                            note="verify passed (no-op apply)",
                            extra={"verify_result": {
                                "imports_ok": v["imports_ok"],
                                "imports_broken": len(v["imports_broken"]),
                                "health_issues": len(v["health_issues"]),
                            }},
                            approved_by="SKB Sakib")
        print(c(f"  -> VERIFIED", GREEN))
    else:
        proposal.transition(pid, "FAILED", note="verify failed")
        proposal.transition(pid, "ROLLED_BACK",
                            note="no-op apply rollback",
                            approved_by="SKB Sakib")
        print(c(f"  -> ROLLED_BACK", RED))
    pause()


def _reject_one():
    from ..ui import (BOLD, GREEN, RED, YELLOW)
    from ..ui import c, clear, header, pause
    clear()
    header("🚫 REJECT PROPOSAL", "")
    for p in proposal.list_by_status("WAITING_APPROVAL"):
        print(f"  #{p['id']:<4} {p['category']}/{p['module']}  "
              f"{(p['problem'] or '')[:50]}")
    pid = input(c("\n  Proposal #: ", BOLD)).strip()
    if not pid.isdigit():
        return
    ok, msg = proposal.transition(int(pid), "REJECTED", actor="SKB Sakib")
    print(c(f"  {'OK ' + msg if ok else 'X ' + msg}", GREEN if ok else RED))
    pause()


def _history():
    from ..ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from ..ui import c, clear, header, pause
    clear()
    header("📜 UPGRADE HISTORY", "Last 30")
    rows = proposal.list_all(30)
    if not rows:
        print(c("\n  (none)", DIM + WHITE)); pause(); return
    for p in rows:
        col = (GREEN if p["status"] in ("VERIFIED",)
               else RED if p["status"] in ("FAILED", "ROLLED_BACK", "REJECTED")
               else YELLOW)
        print(f"  #{p['id']:<4} {c(p['status'], col):<22} "
              f"{p['category']:<10} {p['module']:<12} "
              f"{(p['problem'] or '')[:40]}")
    pause()


def _snapshots():
    from ..ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from ..ui import c, clear, header, pause
    while True:
        clear()
        header("💾 SNAPSHOTS", "Backups for rollback")
        snaps = apply_mod.list_snapshots()
        if not snaps:
            print(c("\n  (none)", DIM + WHITE))
        for i, s in enumerate(snaps[:15], 1):
            print(f"  {i}. {s.name}")
        print()
        print("  1. Take new snapshot")
        print("  2. Rollback to #")
        print("  0. Back")
        ch = input(c("\n  > Select: ", BOLD)).strip()
        if ch == "0":
            break
        if ch == "1":
            a = apply_mod.snapshot_code()
            b = apply_mod.snapshot_db()
            print(c(f"\n  code: {a}", GREEN))
            print(c(f"  db  : {b}", GREEN))
            pause()
        elif ch == "2":
            n = input("  #: ").strip()
            if n.isdigit():
                idx = int(n) - 1
                if 0 <= idx < len(snaps):
                    r = apply_mod.rollback_to(str(snaps[idx]),
                                              approved_by="SKB Sakib")
                    print(c(f"  ok: {r['ok']}", GREEN if r.get("ok") else RED))
                    pause()


def _run_cycle():
    from ..ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from ..ui import c, clear, header, pause
    clear()
    header("🔄 FULL CYCLE", "detect → propose → sandbox → report")
    print(c("\n  running...", DIM + WHITE))
    s = run_full_cycle(actor="SKB Sakib")
    _print_summary(s)
    pause()


def main():
    from ..ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW)
    from ..ui import c, clear, header, pause, section
    while True:
        clear()
        header("🧪 UPGRADE LAB", "Safe, sandboxed, owner-gated")
        section("QUICK STATUS", "📊")
        try:
            pend = len(proposal.pending())
        except Exception:
            pend = 0
        try:
            snaps = len(apply_mod.list_snapshots())
        except Exception:
            snaps = 0
        print(f"  pending proposals : {pend}")
        print(f"  snapshots         : {snaps}")
        print()
        print("  1. Full cycle (detect → propose → sandbox)")
        print("  2. Show pending proposals")
        print("  3. Sandbox-test one proposal")
        print("  4. Approve + apply (owner)")
        print("  5. Reject proposal")
        print("  6. History")
        print("  7. Snapshots (backup / rollback)")
        print("  0. Back")
        ch = input(c("\n  > Select: ", BOLD)).strip()
        if ch == "0":
            break
        elif ch == "1":
            _run_cycle()
        elif ch == "2":
            _list_pending(); pause()
        elif ch == "3":
            _sandbox_one()
        elif ch == "4":
            _approve_one()
        elif ch == "5":
            _reject_one()
        elif ch == "6":
            _history()
        elif ch == "7":
            _snapshots()
        else:
            print(c("  X invalid", RED)); pause()


run = main


if __name__ == "__main__":
    main()
