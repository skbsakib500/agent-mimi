"""Talk to Nusrat - the chairwoman."""
from .bootstrap import bootstrap
from .nusrat import nusrat


def main():
    from ..ui import (BOLD, CYAN, DIM, GREEN, MAGENTA, RED,
                      WHITE, YELLOW)
    from ..ui import c, clear, header, pause
    clear()
    header("🏛  TALK TO NUSRAT", "Chairwoman of the Council")
    try:
        added = bootstrap()
    except Exception as e:
        print(c(f"  bootstrap error: {e}", RED)); pause(); return

    n = nusrat()
    print()
    print(c("  Nusrat is ready.", GREEN))
    if added:
        print(c(f"  (departments added: {', '.join(added)})",
                DIM + WHITE))
    print(c("  Type 'help' for commands, 'exit' to leave.", DIM + WHITE))
    print()
    while True:
        try:
            line = input(c("  you > ", BOLD + CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not line:
            continue
        if line.lower() in ("exit", "quit", "bye"):
            break
        r = n.listen(line, actor="SKB Sakib")
        print()
        for ln in str(r["text"]).splitlines():
            print(c(f"  Nusrat: {ln}", MAGENTA))
        print()
    print(c("  Nusrat has gone quiet.", DIM + WHITE))
    pause()


run = main

if __name__ == "__main__":
    main()
