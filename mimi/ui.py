"""Agent Mimi - terminal UI."""
from datetime import datetime, date
import os, shutil

RESET="\033[0m"; BOLD="\033[1m"; DIM="\033[2m"
CYAN="\033[96m"; BLUE="\033[94m"; GREEN="\033[92m"
YELLOW="\033[93m"; RED="\033[91m"; MAGENTA="\033[95m"
WHITE="\033[97m"; GRAY="\033[90m"
USE_COLOR = os.environ.get("MIMI_NO_COLOR") != "1"

def c(t, color=""): return f"{color}{t}{RESET}" if USE_COLOR else str(t)

def width(default=76):
    try: return max(64, min(shutil.get_terminal_size((default,24)).columns, 100))
    except Exception: return default

def clear(): os.system("clear" if os.name != "nt" else "cls")

def line(ch="-"): return ch * width()

def header(title, subtitle=""):
    W = width()
    print()
    print(c("+" + "-"*(W-2) + "+", MAGENTA))
    print(c("|", MAGENTA) + c(f"  * {title}".ljust(W-1), BOLD+WHITE) + c("|", MAGENTA))
    if subtitle:
        print(c("|", MAGENTA) + c(f"  {subtitle}".ljust(W-1), DIM+WHITE) + c("|", MAGENTA))
    print(c("+" + "-"*(W-2) + "+", MAGENTA))

def section(title, icon=""):
    print()
    print(c(f"  {icon} {title}", BOLD+MAGENTA))
    print(c("  " + "-"*(width()-4), GRAY))

def mimi(text):
    print(c(f"  Mimi: {text}", MAGENTA))

def progress_bar(value, w=28, color=GREEN):
    try: value = max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError): value = 0.0
    f = int(round(w * value / 100))
    return c("#"*f, color) + c("."*(w-f), GRAY) + f" {value:.0f}%"

def mini_bar(value, mx, w=22, color=CYAN):
    try:
        value = max(0.0, float(value)); mx = max(1.0, float(mx))
        ratio = min(1.0, value/mx)
    except (TypeError, ValueError): ratio = 0.0
    f = int(round(w*ratio))
    return c("="*f, color) + c("-"*(w-f), GRAY)

def menu(items, title="MENU"):
    section(title)
    for k, label in items:
        print(f"  {c(str(k).rjust(2), CYAN)}  {label}")
    return input(c("\n  > Select: ", BOLD+WHITE)).strip()

def ask(prompt, default=None):
    s = f" [{default}]" if default is not None else ""
    v = input(f"  {prompt}{s}: ").strip()
    return v if v else default

def ask_int(prompt, default=None, minimum=None, maximum=None, allow_blank=False):
    while True:
        raw = input(f"  {prompt}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not raw and default is not None: return default
        if not raw and allow_blank: return None
        try:
            v = int(raw)
            if minimum is not None and v < minimum: raise ValueError
            if maximum is not None and v > maximum: raise ValueError
            return v
        except ValueError:
            print(c("  X Enter a valid integer.", RED))

def ask_float(prompt, default=None, minimum=None, allow_blank=False):
    while True:
        raw = input(f"  {prompt}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not raw and default is not None: return float(default)
        if not raw and allow_blank: return None
        try:
            v = float(raw)
            if minimum is not None and v < minimum: raise ValueError
            return v
        except ValueError:
            print(c("  X Enter a valid number.", RED))

def ask_date(prompt="Date", default=None, allow_blank=False):
    default = default or date.today().isoformat()
    while True:
        raw = input(f"  {prompt} [{default}]: ").strip()
        if not raw and allow_blank: return None
        v = raw or default
        try:
            datetime.strptime(v, "%Y-%m-%d"); return v
        except ValueError:
            print(c("  X Date must be YYYY-MM-DD.", RED))

def ask_time(prompt="Time", default=None, allow_blank=True):
    while True:
        raw = input(f"  {prompt}" + (f" [{default}]" if default else "") + ": ").strip()
        if not raw and allow_blank: return None
        v = raw or default
        try:
            datetime.strptime(v, "%H:%M"); return v
        except (ValueError, TypeError):
            print(c("  X Time must be HH:MM.", RED))

def pause(msg="Press Enter..."):
    input(c(f"\n  {msg}", DIM+WHITE))

def yes_no(prompt, default=False):
    raw = input(f"  {prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    if not raw: return default
    return raw in ("y","yes","1","true")

def print_rows(rows, columns):
    if not rows:
        print(c("\n  No records found.", YELLOW)); return
    for row in rows:
        print(c("\n" + "-"*min(width(),72), GRAY))
        for key, label in columns:
            v = row[key] if key in row.keys() else ""
            print(f"  {label}: {v}")
    print(c("-"*min(width(),72), GRAY))


def clock_card():
    """Framed date + live time for the dashboard."""
    from datetime import datetime
    now = datetime.now()
    d = now.strftime("%A, %d %b %Y")
    t = now.strftime("%H:%M:%S")
    W = 42
    print()
    print(c("  +" + "-" * W + "+", CYAN))
    print(c("  |", CYAN) + f"  {d}".ljust(W + 1) + c("|", CYAN))
    print(c("  |", CYAN) + "  " + c(t, BOLD + WHITE)
          + " " * (W - len(t) - 2) + c("|", CYAN))
    print(c("  +" + "-" * W + "+", CYAN))
