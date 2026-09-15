"""Auto-learn TUI."""


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, MAGENTA, RED,
                     WHITE, YELLOW)
    from .ui import c, clear, header, menu, pause, section
    from . import learn

    while True:
        clear()
        header("🧠 AUTO-LEARN", "Multi-AI consensus knowledge")
        s = learn.stats()
        print()
        print(f"  Knowledge items : {s['n']}")
        print(f"  Avg confidence  : {s['avg_conf']:.2f}")
        print()
        ch = menu([
            ("1", "Ask + learn (consensus)"),
            ("2", "Browse learned knowledge"),
            ("3", "Search knowledge"),
            ("4", "Delete a knowledge item"),
            ("0", "Exit"),
        ], "AUTO-LEARN MENU")

        if ch == "1":
            q = input(c("  Question: ", BOLD + WHITE)).strip()
            if not q:
                continue
            t = input("  Topic [auto]: ").strip() or None
            print(c("  Consulting AIs and scoring…", DIM + WHITE))
            r = learn.learn_question(q, topic=t)
            if not r.get("ok"):
                print(c(f"  X {r.get('error')}", RED))
                pause(); continue
            print()
            print(c(f"  ✓ Learned from consensus", GREEN + BOLD))
            print(f"  Winner      : {r['winner']} (score {r['score']})")
            print(f"  Confidence  : {r['confidence']}")
            print()
            print(c("  Ranking:", CYAN))
            for item in r["ranking"]:
                print(f"    {item['provider']:<12}  {item['score']}")
            print()
            print(c("  Answer:", CYAN + BOLD))
            for line in str(r["answer"]).splitlines():
                print(f"    {line}")
            pause()
        elif ch == "2":
            rows = learn.all_knowledge()
            clear()
            header("KNOWLEDGE BASE", f"{len(rows)} items")
            for r in rows:
                print(f"\n  #{r['id']}  {c(r['topic'], CYAN)}")
                print(f"      Q: {r['question'][:70]}")
                print(f"      A: {r['snippet'][:70]}…")
                print(c(f"      conf {r['confidence']:.2f}  uses {r['use_count']}",
                        DIM + WHITE))
            pause()
        elif ch == "3":
            q = input(c("  Search: ", BOLD + WHITE)).strip()
            rows = learn.recall(q)
            if not rows:
                print(c("  (no match)", RED))
            for r in rows:
                print(f"\n  #{r['id']} [{r['topic']}] conf={r['confidence']:.2f}")
                print(f"      {r['answer'][:200]}")
            pause()
        elif ch == "4":
            kid = input(c("  Knowledge ID: ", BOLD + WHITE)).strip()
            if kid.isdigit():
                learn.delete(kid)
                print(c("  ✓ Deleted", GREEN))
            pause()
        elif ch == "0":
            break


run = main

if __name__ == "__main__":
    main()
