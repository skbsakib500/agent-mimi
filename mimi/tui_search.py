"""Live filter overlay for list screens."""
import curses


def prompt(stdscr, current_query=""):
    """Return user query or None if cancelled."""
    h, w = stdscr.getmaxyx()
    try:
        curses.curs_set(1)
    except Exception:
        pass
    box_w = min(60, w - 4)
    y0 = h - 4
    x0 = 2

    # Clear a strip
    try:
        stdscr.addstr(y0, x0, " " * box_w, curses.color_pair(8))
        stdscr.addstr(y0 + 1, x0, " " * box_w, curses.color_pair(8))
    except Exception:
        pass

    border = curses.color_pair(9)
    try:
        stdscr.addstr(y0, x0, "╭" + "─" * (box_w - 2) + "╮", border)
        stdscr.addstr(y0 + 1, x0, "╰" + "─" * (box_w - 2) + "╯", border)
    except Exception:
        pass

    query = current_query
    while True:
        try:
            stdscr.addstr(y0, x0 + 2, " / " + query + " " * (box_w - 6),
                          curses.color_pair(4) | curses.A_BOLD)
            stdscr.move(y0, x0 + 4 + len(query))
        except Exception:
            pass
        stdscr.refresh()

        ch = stdscr.getch()
        if ch == 27:  # ESC
            try: curses.curs_set(0)
            except Exception: pass
            return None
        if ch in (10, 13, curses.KEY_ENTER):
            try: curses.curs_set(0)
            except Exception: pass
            return query
        if ch in (curses.KEY_BACKSPACE, 127, 8):
            query = query[:-1]
        elif 32 <= ch < 127:
            query += chr(ch)
