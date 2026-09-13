"""Adaptive terminal helpers."""
import os, shutil, sys

MIN_W = 60
MAX_W = 110
FALLBACK = 78

def cols():
    try:
        c = shutil.get_terminal_size((FALLBACK, 24)).columns
        return max(MIN_W, min(MAX_W, c))
    except Exception:
        return FALLBACK

def rows():
    try:
        return shutil.get_terminal_size((FALLBACK, 24)).lines
    except Exception:
        return 24

def card_w():
    """Width for framed cards: fits in terminal, min 56."""
    return max(56, min(cols() - 2, 96))

def panel_w():
    """Width for tables / heatmap."""
    return cols() - 4

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def hide_cursor():
    if sys.stdout.isatty():
        sys.stdout.write("\033[?25l"); sys.stdout.flush()

def show_cursor():
    if sys.stdout.isatty():
        sys.stdout.write("\033[?25h"); sys.stdout.flush()

def move_up(n):
    if sys.stdout.isatty():
        sys.stdout.write(f"\033[{n}A")

def cls_line():
    if sys.stdout.isatty():
        sys.stdout.write("\033[K")

def is_tty():
    return sys.stdout.isatty()
