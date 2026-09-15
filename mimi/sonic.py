"""V10 Sonic CLI - the unified event-driven interface.

Usage:
  python -m mimi.sonic           interactive menu
  python -m mimi.sonic health    one-shot diagnostic
  python -m mimi.sonic audit     verify audit chain
  python -m mimi.sonic ask "..." one-shot query to Mimi
  python -m mimi.sonic route CMD [k=v ...]
"""
import sys
import time
from datetime import datetime

from .trust.loader import ensure_trusted
from .guardian import audit
from .guardian.permissions import check
from .core.orchestrator import orchestrator


# ──────────── color helpers (no curses; plain ANSI) ────────────

R = "\033[0m"; B = "\033[1m"; D = "\033[2m"
CY = "\033[96m"; BL = "\033[94m"; GR = "\033[92m"
YL = "\033[93m"; RD = "\033[91m"; MG = "\033[95m"; WH = "\033[97m"


def c(t, *codes):
    return "".join(codes) + str(t) + R


def clear():
    import os
    os.system("clear")


def _wrap(s, w):
    out = []
    line = ""
    for word in str(s).split():
        if len(line) + len(word) + 1 > w:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out or [""]


def _banner():
    print()
    print(c("  +==============================================+", MG))
    print(c("  |        MIMI  SUPER  SONIC  MODE              |", MG + B))
    print(c("  |        v10 · Guardian Core active            |", D + WH))
    print(c("  +==============================================+", MG))
    print()


def _footer(status):
    """Print a small status footer."""
    print()
    print(c("  ----------------------------------------------", D + WH))
    if status.get("trust"):
        print(c(f"    trust   : verified", GR))
    else:
        print(c(f"    trust   : NOT VERIFIED", RD))
    if status.get("audit_ok") is not None:
        col = GR if status.get("audit_ok") else RD
        print(c(f"    audit   : {status.get('audit_msg','')}",
                col))
    if status.get("pending") is not None:
        print(c(f"    upgrades: {status['pending']} pending", YL))
    print(c("  ----------------------------------------------", D + WH))


def _status():
    """Collect a quick status dict for the footer."""
    s = {"trust": False, "audit_ok": None, "audit_msg": "",
         "pending": None}
    try:
        s["trust"] = ensure_trusted(fail_closed=False)
    except Exception:
        pass
    try:
        from .guardian.audit import verify_chain
        ok, msg, n = verify_chain()
        s["audit_ok"] = ok
        s["audit_msg"] = f"{msg} ({n} events)"
    except Exception:
        s["audit_ok"] = False
        s["audit_msg"] = "error"
    try:
        from .upgrade import proposal
        s["pending"] = len(proposal.pending())
    except Exception:
        s["pending"] = 0
    return s


# ──────────── actions ────────────

def act_health():
    from .health.diagnostic import run_all
    r = run_all()
    print()
    print(c("  MIMI SUPER SONIC DIAGNOSTIC", B + MG))
    print(c("  " + "-" * 50, D + WH))
    print(f"  OK {r['ok']}   WARN {r['warn']}   "
          f"FAIL {r['fail']}   ({r['elapsed_sec']}s)")
    print(c("  " + "-" * 50, D + WH))
    for sec, items in r["sections"].items():
        print()
        print(c(f"  [{sec}]", B + CY))
        for it in items:
            if it["status"] == "OK":
                mark, col = "OK", GR
            elif it["status"] == "WARN":
                mark, col = "! ", YL
            else:
                mark, col = "X ", RD
            print(c(f"    {mark} {it['name']:<22} {it['detail'][:44]}", col))
    audit.log("sonic_health", actor="sonic", payload={"fail": r["fail"]})


def act_diagnose():
    from .upgrade import detect, proposal
    findings = detect.scan()
    print()
    print(c("  SELF-DIAGNOSIS", B + MG))
    if not findings:
        print(c("  All clear. Nothing to report.", GR))
        return
    for f in findings:
        col = (RD if f["risk"] == "critical"
               else YL if f["risk"] in ("high", "medium")
               else GR)
        print()
        print(c(f"  [{f['risk']}] {f['category']}/{f['module']}", col + B))
        for ln in _wrap(f["problem"], 58):
            print(f"      {ln}")
        print(c(f"      action: {f['proposal']}", D + WH))
    if input(c("\n  Convert to proposals? [y/N]: ")).strip().lower() == "y":
        ids = detect.to_proposals(findings)
        print(c(f"  OK created {len(ids)} proposal(s): {ids}", GR))


def act_upgrade_search():
    from .upgrade import proposal, detect
    try:
        ids = detect.to_proposals()
        print(c(f"  OK created {len(ids)} new proposal(s)", GR))
    except Exception as e:
        print(c(f"  X {type(e).__name__}: {e}", RD))


def act_review_upgrades():
    from .upgrade import proposal
    rows = proposal.pending()
    print()
    print(c("  PENDING UPGRADES", B + MG))
    if not rows:
        print(c("  (none)", D + WH))
        return
    for p in rows:
        col = (RD if p["risk_level"] == "critical"
               else YL if p["risk_level"] in ("high", "medium")
               else GR)
        print(f"\n  #{p['id']:<4} {c(p['status'], CY)}  "
              f"{c(p['risk_level'], col)}  "
              f"{p['category']}/{p['module']}")
        if p["problem"]:
            print(c(f"      problem: {p['problem'][:60]}", D + WH))
        if p["proposal"]:
            print(c(f"      action : {p['proposal'][:60]}", D + WH))


def act_sandbox_test():
    from .upgrade import proposal, sandbox
    act_review_upgrades()
    pid = input(c("\n  Proposal # (blank=cancel): ", B + WH)).strip()
    if not pid.isdigit():
        return
    pid = int(pid)
    p = proposal.get(pid)
    if not p:
        print(c("  X not found", RD)); return
    if p["status"] not in ("PROPOSED", "DETECTED"):
        print(c(f"  X cannot test from {p['status']}", RD)); return
    proposal.transition(pid, "SANDBOX_TESTING")
    print(c(f"  running sandbox for #{pid} ...", D + WH))
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
                                "elapsed": r["elapsed_sec"]}})
        print(c("  -> WAITING_APPROVAL", GR))
    else:
        proposal.transition(pid, "FAILED", note="sandbox failed")
        print(c("  -> FAILED", RD))


def act_approve_apply():
    from .upgrade import proposal, apply as A
    rows = proposal.list_by_status("WAITING_APPROVAL")
    print()
    print(c("  WAITING FOR YOUR APPROVAL", B + MG))
    if not rows:
        print(c("  (none)", D + WH)); return
    for p in rows:
        print(f"\n  #{p['id']:<4} {p['category']}/{p['module']}")
        print(c(f"      problem: {(p['problem'] or '')[:60]}", D + WH))
        print(c(f"      action : {(p['proposal'] or '')[:60]}", D + WH))
    pid = input(c("\n  Proposal #: ", B + WH)).strip()
    if not pid.isdigit():
        return
    pid = int(pid)
    confirm = input(c(f"  Type 'APPROVE {pid}': ", B + YL)).strip()
    if confirm != f"APPROVE {pid}":
        print(c("  cancelled.", RD)); return
    ok, msg = proposal.transition(pid, "APPROVED", actor="SKB Sakib",
                                   approved_by="SKB Sakib")
    if not ok:
        print(c(f"  X {msg}", RD)); return
    print(c(f"  {msg}", GR))
    ok, msg = proposal.transition(pid, "APPLYING", actor="SKB Sakib",
                                   approved_by="SKB Sakib")
    print(c(f"  {msg}", GR if ok else RD))
    v = A.verify(actor="SKB Sakib")
    if v["passed"]:
        proposal.transition(pid, "VERIFIED", note="verify ok",
                            extra={"verify_result": {
                                "imports_ok": v["imports_ok"],
                                "imports_broken": len(v["imports_broken"]),
                                "health_issues": len(v["health_issues"])}},
                            approved_by="SKB Sakib")
        print(c("  -> VERIFIED", GR))
    else:
        proposal.transition(pid, "FAILED", note="verify failed")
        proposal.transition(pid, "ROLLED_BACK", note="auto-rollback",
                            approved_by="SKB Sakib")
        print(c("  -> ROLLED_BACK", RD))


def act_rollback():
    from .upgrade import apply as A
    snaps = A.list_snapshots()
    print()
    print(c("  SNAPSHOTS", B + MG))
    if not snaps:
        print(c("  (none)", D + WH)); return
    for i, s in enumerate(snaps[:15], 1):
        print(f"  {i:>2}. {s.name}")
    n = input(c("\n  # to rollback (blank=cancel): ", B + WH)).strip()
    if not n.isdigit():
        return
    idx = int(n) - 1
    if not (0 <= idx < len(snaps)):
        print(c("  X invalid", RD)); return
    r = A.rollback_to(str(snaps[idx]), approved_by="SKB Sakib")
    print(c(f"  ok: {r['ok']}", GR if r.get("ok") else RD))
    if r.get("restored"):
        print(f"  restored: {r['restored']} files")
    if r.get("verify"):
        print(f"  verify  : {r['verify']['passed']}")


def act_audit():
    from .guardian.audit import verify_chain, tail
    ok, msg, n = verify_chain()
    print()
    print(c("  AUDIT CHAIN", B + MG))
    col = GR if ok else RD
    print(c(f"  {msg} ({n} events)", col))
    print()
    print(c("  last 10:", D + WH))
    for e in tail(10):
        print(f"    {e['ts']}  [{e['actor']}]  {e['event']}")


def act_report():
    from .agents import pa, manager, accountant, advisor
    from .core.orchestrator import orchestrator
    o = orchestrator()
    print()
    print(c("  DAILY INTELLIGENCE REPORT", B + MG))
    print(c(f"  {datetime.now().strftime('%A, %d %b %Y  %H:%M')}",
            D + WH))
    # brief
    try:
        b = o.route("brief", actor="sonic").get("result")
        print()
        print(c(f"  {b['greeting']}, Sakib.", B + CY))
        print(f"    tasks pending : {b['tasks_pending']}")
        print(f"    tasks overdue : {b['tasks_overdue']}")
        print(f"    study 7d      : {b['study_week_h']:.1f}h")
        print(f"    balance       : {b['balance']:,.0f}")
    except Exception as e:
        print(c(f"  brief failed: {e}", RD))
    # plan
    try:
        p = o.route("plan", actor="sonic").get("result")
        print()
        print(c("  TODAY'S PLAN", B + CY))
        for blk in p.get("plan", []):
            print(f"    [{blk['when']:<10}] {blk['action']}")
        print(c(f"  one rule: {p.get('one_rule','')}", D + WH))
    except Exception:
        pass


def act_ask(question=None):
    from .agent import Agent
    if question is None:
        question = input(c("\n  Ask Mimi: ", B + CY)).strip()
    if not question:
        return
    print(c("\n  Mimi is thinking...", D + WH))
    try:
        a = Agent()
        reply = a.respond(question)
    except Exception as e:
        reply = f"[error: {type(e).__name__}: {e}]"
    print()
    for ln in str(reply).splitlines():
        print(c(f"  Mimi: {ln}", MG))
    audit.log("sonic_ask", actor="sonic",
              payload={"len": len(question)})


def act_route(command, args=None, approved_by=None):
    o = orchestrator()
    r = o.route(command, args=args or {}, actor="sonic",
                approved_by=approved_by)
    if r.get("ok"):
        print(c(f"  OK [{r.get('specialist')}]", GR))
        print(f"  result: {r.get('result')}")
    else:
        print(c(f"  X {r.get('reason')}", RD))




def act_council():
    from .council.bootstrap import bootstrap
    bootstrap()
    from .council.council import council
    co = council()
    depts = co.all()
    print()
    print(c("  COUNCIL OF BRAINS", B + MG))
    print(c("  " + "-" * 50, D + WH))
    for d in depts:
        print(f"    [{d.PRIORITY}] {d.NAME:<12} {d.ROLE}")
    print()
    print(c(f"  Total: {len(depts)} departments + Nusrat", GR))


def act_nusrat(question=None):
    from .council.bootstrap import bootstrap
    bootstrap()
    from .council.nusrat import nusrat
    n = nusrat()
    if question is None:
        question = input(c("\n  Talk to Nusrat: ", B + CY)).strip()
    if not question:
        return
    r = n.listen(question, actor="SKB Sakib")
    print()
    for ln in str(r["text"]).splitlines():
        print(c(f"  Nusrat: {ln}", MG))




def act_ai_chat():
    """Launch multi-AI chat."""
    from .ai_chat_tui import main
    main()


def act_modes():
    from .persona_tui import main
    main()


def act_learn():
    from .learn_tui import main
    main()


def act_telegram():
    print()
    print(c("  TELEGRAM BOT", B + MG))
    print(c("  " + "-" * 40, D + WH))
    try:
        from .telegram_bot import is_configured
        if not is_configured():
            print(c("  X not configured", RD))
            print("  Set telegram_bot_token and telegram_chat_id")
            return
        print(c("  ✓ configured", GR))
        print()
        print("  start:  python -m mimi.telegram_bot")
        print("  test:   python -m mimi.telegram_bot test")
        print("  whoami: python -m mimi.telegram_bot whoami")
    except Exception as e:
        print(c(f"  X {e}", RD))


def act_location():
    from .location_tui import main
    main()


def act_daemon():
    from .daemon import status, stop_daemon, run_forever
    print()
    print(c("  DAEMON", B + MG))
    print(c("  " + "-" * 40, D + WH))
    st = status()
    if st.get("running"):
        print(c(f"  ✓ running (pid {st['pid']})", GR))
        if input("  stop? [y/N]: ").strip().lower() == "y":
            ok, msg = stop_daemon()
            print(f"  {msg}")
    else:
        print(c("  · not running", D + WH))
        print()
        print("  start: python -m mimi.daemon start")
        print("  test:  python -m mimi.daemon test")



# ──────────── menu ────────────

MENU = [
    ("1",  "Full Health Scan",           act_health),
    ("2",  "Self Diagnose",              act_diagnose),
    ("3",  "Search Upgrades",            act_upgrade_search),
    ("4",  "Review Pending Upgrades",    act_review_upgrades),
    ("5",  "Sandbox Test",               act_sandbox_test),
    ("6",  "Approve + Apply (owner)",    act_approve_apply),
    ("7",  "Rollback to Snapshot",       act_rollback),
    ("8",  "System Audit",               act_audit),
    ("9",  "Daily Intelligence Report",  act_report),
    ("10", "Talk to Mimi",               act_ask),
    ("0",  "Exit",                       None),
]


def menu():
    # ensure trust first
    try:
        ensure_trusted(fail_closed=True)
    except RuntimeError as e:
        print()
        print(c("  X TRUST CHECK FAILED", RD + B))
        print(c(f"  {e}", RD))
        print()
        print(c("  Fix: python -m mimi.trust.signer resign", YL))
        return 2

    while True:
        clear()
        _banner()
        st = _status()
        print(c("  MAIN MENU", B + CY))
        print()
        for key, label, _ in MENU:
            if key == "0":
                continue
            print(f"    [{key:>2}] {label}")
        print()
        print(f"    [ 0] Exit")
        _footer(st)
        ch = input(c("\n  > Select: ", B + WH)).strip()
        if ch == "0":
            print(c("\n  Sonic mode closed. Your data is intact.", D + WH))
            audit.log("sonic_exit", actor="sonic")
            return 0
        fn = None
        for key, _, f in MENU:
            if key == ch:
                fn = f
                break
        if fn is None:
            print(c("  X invalid", RD))
            time.sleep(0.6)
            continue
        try:
            fn()
        except KeyboardInterrupt:
            print(c("\n  (interrupted)", YL))
        except Exception as e:
            print(c(f"  X {type(e).__name__}: {e}", RD))
        try:
            input(c("\n  Enter to return ...", D + WH))
        except (EOFError, KeyboardInterrupt):
            pass


# ──────────── CLI dispatch ────────────

def _kv_pairs(argv):
    out = {}
    for a in argv:
        if "=" in a:
            k, v = a.split("=", 1)
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            out[k.strip()] = v
    return out


def main():
    argv = sys.argv[1:]
    if not argv:
        return menu()
    cmd = argv[0].lower()
    if cmd == "menu":
        return menu()
    if cmd == "health":
        act_health(); return 0
    if cmd == "audit":
        act_audit(); return 0
    if cmd == "diagnose":
        act_diagnose(); return 0
    if cmd == "report":
        act_report(); return 0
    if cmd == "council":
        act_council(); return 0
    if cmd == "ai":
        act_ai_chat(); return 0
    if cmd == "modes":
        act_modes(); return 0
    if cmd == "learn":
        act_learn(); return 0
    if cmd == "tg":
        act_telegram(); return 0
    if cmd == "loc":
        act_location(); return 0
    if cmd == "daemon":
        act_daemon(); return 0
    if cmd == "nusrat":
        act_nusrat(" ".join(argv[1:]) or None); return 0
    if cmd == "ask":
        act_ask(" ".join(argv[1:]) or None); return 0
    if cmd == "route":
        if len(argv) < 2:
            print("usage: route <command> [key=value ...]"); return 1
        act_route(argv[1], _kv_pairs(argv[2:]),
                  approved_by="SKB Sakib")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
