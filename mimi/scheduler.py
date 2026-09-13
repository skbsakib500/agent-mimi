"""Agent Mimi - automation cycle."""
from datetime import datetime
from .monitors import collect, evaluate
from .recommendations import save_all
from . import notify


def run_cycle(push=True):
    m = collect()
    rules = evaluate(m)
    created = save_all(rules)
    if push and rules:
        try:
            critical = [r for r in rules if r.severity == "critical"]
            if critical:
                notify.send("Mimi alert",
                            "; ".join(r.title for r in critical)[:180],
                            priority="high", sound=True, vibrate=True)
            else:
                notify.send("Mimi check-in",
                            f"{len(rules)} rule(s) triggered",
                            priority="default")
        except Exception:
            pass
    return {"timestamp": datetime.now().isoformat(timespec="seconds"),
            "metrics": m, "rules": rules, "created": created}


def print_cycle(result):
    print()
    print("=" * 60)
    print("AUTOMATION CYCLE")
    print("=" * 60)
    print(f"Time: {result['timestamp']}")
    print(f"Rules triggered: {len(result['rules'])}")
    print(f"New recommendations: {result['created']}")
    if result["rules"]:
        print()
        print("EVENTS")
        for r in result["rules"]:
            print(f"  [{r.severity.upper()}] {r.title}")
            print(f"      {r.message}")
    else:
        print("\nNo rules triggered.")
    print("=" * 60)
