"""Agent Mimi - live clock, Dhaka time."""
from datetime import datetime, timedelta, timezone
import time, sys, os, select

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Dhaka")
    ZONE_LABEL = "Dhaka, Bangladesh  ·  UTC+06:00"
except Exception:
    TZ = timezone(timedelta(hours=6))
    ZONE_LABEL = "Dhaka, Bangladesh  ·  UTC+06:00"

USE = os.environ.get("MIMI_NO_COLOR") != "1"
R="\033[0m"; B="\033[1m"; D="\033[2m"
CY="\033[96m"; GR="\033[92m"; YL="\033[93m"
WH="\033[97m"; MG="\033[95m"

def c(t, *codes):
    if not USE: return str(t)
    return "".join(codes) + str(t) + R

WD = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
MO = ["January","February","March","April","May","June",
      "July","August","September","October","November","December"]

def parts():
    n = datetime.now(TZ)
    return {
        "hh": n.strftime("%H"),
        "mm": n.strftime("%M"),
        "ss": n.strftime("%S"),
        "date": f"{WD[n.weekday()]}, {n.day:02d} {MO[n.month-1]} {n.year}",
    }

def render(width=54):
    t = parts()
    inner = width - 4
    top = "  " + c("╭" + "─" * (width - 2) + "╮", CY)
    bot = "  " + c("╰" + "─" * (width - 2) + "╯", CY)

    def row(txt, color=""):
        pad = txt + " " * max(0, inner - len(txt))
        body = c(pad, *([color] if color else []))
        return "  " + c("│", CY) + "  " + body + "  " + c("│", CY)

    time_line = f"{t['hh']} : {t['mm']} : {t['ss']}"
    return [
        top,
        row(""),
        row("HI, BOSS SKB SAKIB", B + MG),
        row(""),
        row(time_line, B + GR),
        row(t["date"], WH),
        row(ZONE_LABEL, D + WH),
        row(""),
        bot,
    ]

def _key_hit():
    r, _, _ = select.select([sys.stdin], [], [], 0)
    return bool(r)

def live(duration=5, width=54):
    lines = render(width)
    n = len(lines)
    for ln in lines:
        print(ln, flush=True)

    import termios, tty
    fd = sys.stdin.fileno()
    old = None
    try:
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    except Exception:
        old = None

    start = time.time()
    try:
        while time.time() - start < duration:
            time.sleep(0.2)
            if old is not None and _key_hit():
                try: sys.stdin.read(1)
                except Exception: pass
                break
            sys.stdout.write(f"\033[{n}A")
            for ln in render(width):
                sys.stdout.write("\033[K" + ln + "\n")
            sys.stdout.flush()
    finally:
        if old is not None:
            try: termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception: pass
    print()

def once(width=54):
    for ln in render(width):
        print(ln)

def main():
    live(8)

run = main
