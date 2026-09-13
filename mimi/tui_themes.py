"""TUI themes."""
import curses

THEMES = {
    "midnight": {
        "HEADER":  (curses.COLOR_WHITE,   curses.COLOR_BLUE),
        "SIDEBAR": (curses.COLOR_CYAN,    -1),
        "SEL":     (curses.COLOR_BLACK,   curses.COLOR_MAGENTA),
        "ACCENT":  (curses.COLOR_MAGENTA, -1),
        "GOOD":    (curses.COLOR_GREEN,   -1),
        "WARN":    (curses.COLOR_YELLOW,  -1),
        "BAD":     (curses.COLOR_RED,     -1),
        "DIM":     (curses.COLOR_WHITE,   -1),
        "BORDER":  (curses.COLOR_CYAN,    -1),
        "CARD":    (curses.COLOR_WHITE,   -1),
    },
    "sunset": {
        "HEADER":  (curses.COLOR_BLACK,   curses.COLOR_YELLOW),
        "SIDEBAR": (curses.COLOR_YELLOW,  -1),
        "SEL":     (curses.COLOR_BLACK,   curses.COLOR_RED),
        "ACCENT":  (curses.COLOR_RED,     -1),
        "GOOD":    (curses.COLOR_YELLOW,  -1),
        "WARN":    (curses.COLOR_RED,     -1),
        "BAD":     (curses.COLOR_RED,     -1),
        "DIM":     (curses.COLOR_WHITE,   -1),
        "BORDER":  (curses.COLOR_YELLOW,  -1),
        "CARD":    (curses.COLOR_WHITE,   -1),
    },
    "forest": {
        "HEADER":  (curses.COLOR_BLACK,   curses.COLOR_GREEN),
        "SIDEBAR": (curses.COLOR_GREEN,   -1),
        "SEL":     (curses.COLOR_BLACK,   curses.COLOR_WHITE),
        "ACCENT":  (curses.COLOR_GREEN,   -1),
        "GOOD":    (curses.COLOR_GREEN,   -1),
        "WARN":    (curses.COLOR_YELLOW,  -1),
        "BAD":     (curses.COLOR_RED,     -1),
        "DIM":     (curses.COLOR_WHITE,   -1),
        "BORDER":  (curses.COLOR_GREEN,   -1),
        "CARD":    (curses.COLOR_WHITE,   -1),
    },
}

# Numeric slot → semantic name (matches CP_* order in tui.py)
SLOTS = ["HEADER", "SIDEBAR", "SEL", "ACCENT",
         "GOOD", "WARN", "BAD", "DIM", "BORDER", "CARD"]

CURRENT = "midnight"


def get_current():
    return CURRENT


def set_current(name):
    global CURRENT
    if name in THEMES:
        CURRENT = name
        return True
    return False


def cycle():
    keys = list(THEMES.keys())
    i = keys.index(CURRENT)
    set_current(keys[(i + 1) % len(keys)])
    return CURRENT


def apply():
    """Reinitialize curses color pairs from CURRENT theme."""
    t = THEMES[CURRENT]
    for i, slot in enumerate(SLOTS, start=1):
        fg, bg = t[slot]
        try:
            curses.init_pair(i, fg, bg if bg != -1 else curses.COLOR_BLACK)
        except Exception:
            try:
                curses.init_pair(i, fg, curses.COLOR_BLACK)
            except Exception:
                pass
