"""Level-up celebration."""
import time, os

USE = os.environ.get("MIMI_NO_COLOR") != "1"
R="\033[0m"; B="\033[1m"; D="\033[2m"
CY="\033[96m"; GR="\033[92m"; YL="\033[93m"; MG="\033[95m"; WH="\033[97m"

def c(t, *codes):
    if not USE: return str(t)
    return "".join(codes) + str(t) + R

BANNER = r"""
   __    __  ___  __  __    __   __  ___
  / /   / / / _ \/ / / /   / /  / / / _ \
 / /___/ / / __/ /_/ /   / /__/ / / ___/
/_____/_/ /____/\____/  /____/_/ /_/
"""


def show(level, title, xp):
    os.system("clear") if os.name != "nt" else os.system("cls")
    print()
    for line in BANNER.strip("\n").splitlines():
        print(c(line, B + MG))
    print()
    print(c(f"        LEVEL {level}  ·  {title}", B + GR))
    print(c(f"        {xp} XP total", D + WH))
    print()
    for i in range(4):
        print(c("        " + "★ " * 5, YL))
        time.sleep(0.15)
    print()
    time.sleep(1.0)


def maybe_celebrate(gained, leveled_up, level_info_fn):
    """Show XP toast; celebrate if leveled up."""
    if gained > 0:
        print(c(f"  +{gained} XP", GR + B), end="")
    if leveled_up:
        info = level_info_fn()
        print()
        time.sleep(0.4)
        show(info["level"], info["title"], info["xp"])
    else:
        print()
