"""Persona switcher."""


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, MAGENTA, RED,
                     WHITE, YELLOW)
    from .ui import c, clear, header, menu, pause
    from . import personas

    while True:
        clear()
        header("🎭 COMPANION MODES", "Nusrat's tone")
        cur = personas.current_name()
        print()
        print(f"  Current: {c(cur.upper(), GREEN + BOLD)}")
        print()
        items = []
        for i, p in enumerate(personas.list_all(), 1):
            mark = "●" if p["id"] == cur else "○"
            items.append((str(i), f"{mark} {p['icon']} {p['name']:<12} "
                                  f"({p['bn']})"))
        items.append(("0", "Exit"))
        ch = menu(items, "SELECT MODE")
        if ch == "0":
            break
        if ch.isdigit():
            idx = int(ch) - 1
            all_p = personas.list_all()
            if 0 <= idx < len(all_p):
                personas.set_persona(all_p[idx]["id"])
                print(c(f"  ✓ Mode set: {all_p[idx]['name']}", GREEN))
                pause()
        if ch == "c":
            personas.cycle()
            print(c(f"  ✓ Cycled to {personas.current_name()}", GREEN))
            pause()


run = main

if __name__ == "__main__":
    main()
