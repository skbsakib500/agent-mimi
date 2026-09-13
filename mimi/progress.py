"""Progress / XP / Badges menu."""
from . import xp, badges
from .ui import GREEN, RED, YELLOW, c, clear, header, pause, section


def _bar(pct, w=40):
    filled = int(round(w * pct / 100))
    color = GREEN if pct < 60 else YELLOW if pct < 90 else GREEN
    return c("█" * filled, color) + c("░" * (w - filled), "\033[2m\033[97m")


def show():
    clear()
    header("PROGRESS", "XP · Level · Badges")
    info = xp.level_info()
    print()
    print(f"  {c('LEVEL ' + str(info['level']), GREEN + '\033[1m')}  ·  "
          f"{c(info['title'], '\033[95m\033[1m')}")
    print(f"  {info['xp']} XP total")
    print()
    print(f"  {_bar(info['pct'], 42)}  {info['pct']:.0f}%")
    if info["next_at"]:
        print(f"  Next level in {info['to_next']} XP (at {info['next_at']})")
    else:
        print(c("  MAX LEVEL", GREEN))

    section("BADGES", "🏅")
    got = badges.unlocked()
    have = len(got)
    total = len(badges.BADGES)
    print(f"  Unlocked: {have}/{total}\n")
    for code, icon, label, desc in badges.BADGES:
        mark = c("✓", GREEN) if code in got else c("·", "\033[2m\033[97m")
        line = f"  {mark} {icon} {label}"
        print(line + (f"  {c(desc, '\033[2m\033[97m')}" if code in got else ""))


def main():
    while True:
        show()
        print()
        print("  1. Refresh  2. Check badges  3. Reset XP  0. Back")
        ch = input(c("\n  > Select: ")).strip()
        if ch == "1":
            continue
        if ch == "2":
            new = badges.check_all()
            if new:
                print(c(f"\n  New: {', '.join(new)}", GREEN))
            else:
                print(c("\n  No new badges.", YELLOW))
            pause()
        elif ch == "3":
            xp.reset()
            print(c("\n  XP reset.", RED))
            pause()
        elif ch == "0":
            break


run = main
