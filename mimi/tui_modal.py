"""Modal detail popup for TUI."""
import curses


def _wrap(text, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def show(stdscr, title, fields, width=66):
    """Show a centered modal. fields = list of (label, value).
    Returns when user presses Esc/Enter/q."""
    h, w = stdscr.getmaxyx()
    bw = min(width, w - 4)
    # compute body lines
    body = []
    for label, value in fields:
        if label is None:
            body.append(("", ""))
        else:
            body.append((label, str(value)))
    max_val_len = max([len(v) for _, v in body] + [10])
    wrap_w = bw - 6 - 14
    wrapped = []
    for label, value in body:
        if not label and not value:
            wrapped.append(("", ""))
            continue
        for i, line in enumerate(_wrap(value, wrap_w)):
            wrapped.append((label if i == 0 else "", line))

    bh = min(len(wrapped) + 6, h - 4)
    y0 = (h - bh) // 2
    x0 = (w - bw) // 2

    # Dim background
    try:
        for yy in range(h):
            stdscr.addstr(yy, 0, " " * w, curses.color_pair(8))
    except Exception:
        pass

    border = curses.color_pair(9)
    try:
        stdscr.addstr(y0, x0, "╭" + "─" * (bw - 2) + "╮", border)
        stdscr.addstr(y0 + bh - 1, x0, "╰" + "─" * (bw - 2) + "╯", border)
        for i in range(1, bh - 1):
            stdscr.addstr(y0 + i, x0, "│", border)
            stdscr.addstr(y0 + i, x0 + bw - 1, "│", border)
        stdscr.addstr(y0, x0 + 3, f" {title} ",
                      curses.color_pair(4) | curses.A_BOLD)
    except Exception:
        pass

    row = y0 + 2
    for label, value in wrapped:
        if row >= y0 + bh - 1:
            break
        try:
            if label:
                stdscr.addstr(row, x0 + 2, label.ljust(12) + ": ",
                              curses.color_pair(4) | curses.A_BOLD)
                stdscr.addstr(row, x0 + 16, value[: bw - 18],
                              curses.color_pair(10))
            elif value:
                stdscr.addstr(row, x0 + 16, value[: bw - 18],
                              curses.color_pair(10))
        except Exception:
            pass
        row += 1

    try:
        stdscr.addstr(y0 + bh - 2, x0 + 3,
                      " Press Enter or Esc to close ",
                      curses.color_pair(8) | curses.A_DIM)
    except Exception:
        pass

    stdscr.nodelay(False)
    try:
        while True:
            ch = stdscr.getch()
            if ch in (27, 10, 13, ord('q'), ord('Q')):
                break
    finally:
        stdscr.nodelay(True)


def confirm(stdscr, title, message):
    """Yes/No modal. Returns True if confirmed."""
    h, w = stdscr.getmaxyx()
    bw = min(60, w - 4)
    bh = 8
    y0 = (h - bh) // 2
    x0 = (w - bw) // 2

    try:
        for yy in range(h):
            stdscr.addstr(yy, 0, " " * w, curses.color_pair(8))
    except Exception:
        pass

    border = curses.color_pair(9)
    try:
        stdscr.addstr(y0, x0, "╭" + "─" * (bw - 2) + "╮", border)
        stdscr.addstr(y0 + bh - 1, x0, "╰" + "─" * (bw - 2) + "╯", border)
        for i in range(1, bh - 1):
            stdscr.addstr(y0 + i, x0, "│", border)
            stdscr.addstr(y0 + i, x0 + bw - 1, "│", border)
        stdscr.addstr(y0, x0 + 3, f" {title} ",
                      curses.color_pair(7) | curses.A_BOLD)
    except Exception:
        pass

    for i, line in enumerate(_wrap(message, bw - 6)[:3]):
        try:
            stdscr.addstr(y0 + 2 + i, x0 + 3, line, curses.color_pair(10))
        except Exception:
            pass

    try:
        stdscr.addstr(y0 + bh - 2, x0 + 3,
                      " [y] Yes   [n] No ",
                      curses.color_pair(4) | curses.A_BOLD)
    except Exception:
        pass

    stdscr.nodelay(False)
    try:
        while True:
            ch = stdscr.getch()
            if ch in (ord('y'), ord('Y')):
                return True
            if ch in (ord('n'), ord('N'), 27):
                return False
    finally:
        stdscr.nodelay(True)
