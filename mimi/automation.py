"""Agent Mimi - automation menu."""
from .scheduler import run_cycle, print_cycle
from .recommendations import recent
from .ui import RED, c, clear, header, menu, pause

def show_metrics(result):
    clear()
    header("AUTOMATION METRICS", "Live data")
    m = result["metrics"]
    if m.get("study"):
        print(f"  Study 7d: {m['study']['hours']:.1f}h")
    if m.get("goals"):
        print(f"  Avg goal progress: {m['goals']['avg_progress']:.1f}%")
    if m.get("missions"):
        print(f"  Avg mission progress: {m['missions']['avg_progress']:.1f}%")
    if m.get("tasks"):
        print(f"  Overdue: {m['tasks']['overdue']}  Due soon: {m['tasks']['due_soon']}")
    if m.get("finance"):
        print(f"  Balance: {m['finance']['balance']:,.2f}")
    if m.get("sleep"):
        print(f"  Avg sleep 7d: {m['sleep']['avg_minutes']/60:.1f}h")

def show_recent():
    clear()
    header("RECENT RECOMMENDATIONS", "Latest 20")
    rows = recent(20)
    if not rows:
        print(c("\n  No recommendations yet.", RED))
        return
    for r in rows:
        print(f"\n  #{r['id']} [{r['priority'].upper()}] {r['title']}")
        print(f"  {r['message']}")
        print(f"  Source: {r['source_module']}   Read: {'Yes' if r['is_read'] else 'No'}")

def main():
    while True:
        ch = menu([("1","Run automation cycle"),
                   ("2","Show current metrics"),
                   ("3","Recent recommendations"),
                   ("0","Exit")], "AUTOMATION ENGINE")
        if ch == "1":
            clear()
            print_cycle(run_cycle())
        elif ch == "2":
            show_metrics(run_cycle())
        elif ch == "3":
            show_recent()
        elif ch == "0":
            break
        else:
            print(c("  X Invalid.", RED))
        if ch != "0":
            pause()

run = main
