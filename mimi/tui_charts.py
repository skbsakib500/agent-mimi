"""Charts drawn inside curses windows."""
import curses
from datetime import date, timedelta
from .database import fetch_all, fetch_one


def hbar(pct, width):
    """Return '█░' bar string of given width."""
    pct = max(0.0, min(100.0, pct))
    f = int(round(width * pct / 100))
    return "█" * f + "░" * (width - f)


def sparkline(values):
    """Return single-line sparkline using ▁▂▃▄▅▆▇█."""
    chars = " ▁▂▃▄▅▆▇█"
    if not values:
        return ""
    mx = max(values) or 1
    mn = min(values)
    rng = (mx - mn) or 1
    out = []
    for v in values:
        idx = int((v - mn) / rng * (len(chars) - 1))
        out.append(chars[idx])
    return "".join(out)


def draw_study_trend(stdscr, y, x, h, w):
    """Draw a 14-day study bar chart."""
    try:
        rows = fetch_all("""
            SELECT study_date, COALESCE(SUM(duration_minutes),0) AS m
            FROM study_sessions
            WHERE study_date >= date('now','-13 days')
            GROUP BY study_date""")
    except Exception:
        rows = []
    by_date = {r["study_date"]: r["m"] for r in rows}

    today = date.today()
    vals = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        vals.append((d.strftime("%a")[:3], by_date.get(d.isoformat(), 0)))

    max_m = max([v for _, v in vals] + [1])
    n = len(vals)
    plot_h = max(3, h - 3)
    bar_w = max(1, (w - 2) // n)

    # Grid: for each row, print either filled or empty cell
    for row in range(plot_h):
        ry = y + row
        line = ""
        threshold_row = plot_h - row  # top row = plot_h
        for label, m in vals:
            filled = int(round(m / max_m * plot_h))
            line += "█" * bar_w if filled >= threshold_row else " " * bar_w
        try:
            stdscr.addstr(ry, x, line[:w - 1])
        except Exception:
            pass

    # Axis labels
    try:
        stdscr.addstr(y + plot_h, x, "-" * min(w - 1, n * bar_w))
    except Exception:
        pass
    label_line = ""
    for label, _ in vals:
        label_line += label[:bar_w].center(bar_w)
    try:
        stdscr.addstr(y + plot_h + 1, x, label_line[:w - 1],
                      curses.color_pair(8) | curses.A_DIM)
    except Exception:
        pass


def draw_xp_spark(stdscr, y, x, w):
    """Sparkline of last 7 days of study minutes as XP proxy."""
    try:
        rows = fetch_all("""
            SELECT study_date, COALESCE(SUM(duration_minutes),0) AS m
            FROM study_sessions
            WHERE study_date >= date('now','-6 days')
            GROUP BY study_date""")
    except Exception:
        rows = []
    by = {r["study_date"]: r["m"] for r in rows}
    today = date.today()
    vals = [by.get((today - timedelta(days=i)).isoformat(), 0) for i in range(6, -1, -1)]
    line = sparkline(vals)
    try:
        stdscr.addstr(y, x, f"7d trend: {line}", curses.color_pair(4) | curses.A_BOLD)
    except Exception:
        pass


def draw_finance_bars(stdscr, y, x, w, income, expense):
    """Two horizontal bars for income / expense."""
    mx = max(income, expense, 1)
    bar_w = max(10, w - 20)
    try:
        stdscr.addstr(y, x, "Income ", curses.color_pair(4) | curses.A_BOLD)
        b1 = hbar(income / mx * 100, bar_w)
        stdscr.addstr(y, x + 8, b1[:bar_w], curses.color_pair(5))
        stdscr.addstr(y, x + 10 + bar_w, f"{income:,.0f}", curses.color_pair(5) | curses.A_BOLD)

        stdscr.addstr(y + 1, x, "Expense", curses.color_pair(4) | curses.A_BOLD)
        b2 = hbar(expense / mx * 100, bar_w)
        stdscr.addstr(y + 1, x + 8, b2[:bar_w], curses.color_pair(7))
        stdscr.addstr(y + 1, x + 10 + bar_w, f"{expense:,.0f}", curses.color_pair(7) | curses.A_BOLD)
    except Exception:
        pass
