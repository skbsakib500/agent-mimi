"""Multi-AI chat - terminal UI."""
from .ai_chat import ChatSession
from .multi_ai import available_providers, status, PROVIDERS


def _pick_provider():
    """Ask user which provider(s) to use."""
    avail = available_providers()
    if not avail:
        print("  X No AI providers configured.")
        print("  Set keys: 7 > API Keys > 1")
        return None

    print()
    print("  Available providers:")
    for i, p in enumerate(avail, 1):
        mark = "✓"
        name = PROVIDERS[p]["name"]
        print(f"    {i}. {mark} {name:<14} ({p})")
    print()
    print("    a. ALL (parallel — ask everyone)")
    print("    0. Back")
    choice = input("\n  > Select: ").strip().lower()

    if choice == "0":
        return None
    if choice == "a":
        return avail
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(avail):
            return [avail[idx]]
    return None


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, MAGENTA, RED,
                     WHITE, YELLOW)
    from .ui import c, clear, header, pause

    clear()
    header("🧠 MULTI-AI CHAT", "Talk to one — or all — AIs")

    print()
    print("  Status:")
    for p, ok in status().items():
        name = PROVIDERS[p]["name"]
        mark = c("✓", GREEN) if ok else c("·", DIM + WHITE)
        print(f"    {mark} {name}")

    providers = _pick_provider()
    if not providers:
        return

    session = ChatSession()
    clear()
    header("🧠 AI CHAT", f"{', '.join(providers)}  ·  'exit' to leave")
    print(c("  Type 'clear' to reset · 'multi' to toggle all · 'exit' to leave",
            DIM + WHITE))
    print()

    all_mode = len(providers) > 1

    while True:
        try:
            q = input(c("  you > ", BOLD + CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit", "bye"):
            break
        if q.lower() == "clear":
            session.clear()
            print(c("  (history cleared)", DIM + WHITE))
            continue
        if q.lower() == "multi":
            all_mode = not all_mode
            print(c(f"  (all-mode: {all_mode})", DIM + WHITE))
            continue

        print(c("  ⋯ thinking", DIM + WHITE))

        if all_mode:
            replies = session.ask_all(q, providers=providers)
            print()
            for provider, reply in replies.items():
                name = PROVIDERS[provider]["name"]
                color = {"deepseek": CYAN, "groq": GREEN,
                         "gemini": MAGENTA, "openai": GREEN,
                         "anthropic": YELLOW}.get(provider, WHITE)
                print(c(f"  ╭─ {name} ────", color + BOLD))
                for line in str(reply).splitlines():
                    print(c(f"  │ {line}", color))
                print(c(f"  ╰──────", color + BOLD))
                print()
        else:
            p = providers[0]
            r = session.ask_one(q, provider=p)
            name = PROVIDERS[p]["name"]
            for line in str(r).splitlines():
                print(c(f"  {name} > {line}", GREEN))
            print()

    clear()
    print(c("  AI Chat closed.", DIM + WHITE))
    print(c(f"  Session: {session.stats()}", DIM + WHITE))


run = main

if __name__ == "__main__":
    main()
