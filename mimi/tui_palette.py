"""Fuzzy command palette for TUI."""
import curses

COMMANDS = [
    ("dash",     "Go to Dashboard",          "mimi.tui"),
    ("goals",    "Open Goals editor",        "mimi.goals"),
    ("missions", "Open Missions editor",     "mimi.missions"),
    ("tasks",    "Open Tasks editor",        "mimi.tasks"),
    ("study",    "Open Study editor",        "mimi.study"),
    ("finance",  "Open Finance",             "mimi.finance"),
    ("debts",    "Open Debts",               "mimi.debts"),
    ("journal",  "Open Journal",             "mimi.journal"),
    ("daily",    "Open Daily log",           "mimi.daily"),
    ("pomo",     "Start Pomodoro",           "mimi.pomodoro"),
    ("talk",     "Talk to Mimi (agent)",     "mimi.agent"),
    ("brief",    "Daily Briefing",           "mimi.briefing"),
    ("plan",     "AI Daily Plan",             "mimi.ai_plan"),
    ("review",   "Weekly AI Review",          "mimi.ai_review"),
    ("predict",  "Predictive warnings",       "mimi.predict"),
    ("voice",    "Voice command",             "mimi.voice"),
    ("vision",   "Scan receipt (vision)",     "mimi.vision"),
    ("sugg",     "Smart Suggestions",        "mimi.suggest"),
    ("insights", "Intelligence center",      "mimi.intelligence"),
    ("analytics","Analytics report",         "mimi.analytics"),
    ("auto",     "Run automation cycle",     "mimi.automation"),
    ("prog",     "Progress / XP / Badges",   "mimi.progress"),
    ("badges",   "Badges list",              "mimi.badges"),
    ("backup",   "Backup database",          "mimi.backup"),
    ("export",   "Export JSON/CSV",          "mimi.export"),
    ("report",   "Weekly HTML report",       "mimi.report"),
    ("health",   "Module health",            "mimi.module_health"),
    ("sys",      "System health",            "mimi.system_health"),
    ("keys",     "API keys",                 "mimi.api_manager"),
    ("gemini",   "Gemini chat",              "mimi.api_gemini"),
    ("groq",     "Groq chat",                "mimi.api_groq"),
    ("weather",  "Weather",                  "mimi.api_weather"),
    ("notify",   "Notification setup",       "mimi.notify_setup"),
    ("voice",    "Text to speech",           "mimi.speak"),
    ("data",     "Data manager (delete)",    "mimi.data_manager"),
    ("theme",    "Cycle TUI theme",          "__THEME__"),
    ("quit",     "Exit TUI",                 "__QUIT__"),
]


def _plugin_commands():
    """Return dynamic commands from installed plugins."""
    try:
        from .plugins import discover
        out = []
        for p in discover():
            if not p.get("runnable"):
                continue
            key = "plug-" + p["name"].lower().replace(" ", "-")
            label = f"[plugin] {p['name']}"
            out.append((key, label, f"__PLUGIN__:{p['name']}"))
        return out
    except Exception:
        return []


def _fuzzy_score(query, text):
    q = query.lower()
    t = text.lower()
    if not q:
        return 1
    if q in t:
        return 100 - t.index(q)
    # subsequence
    i = 0
    for ch in t:
        if i < len(q) and ch == q[i]:
            i += 1
    if i == len(q):
        return 50 - len(t)
    return 0


def _draw(stdscr, query, sel, filtered, theme_apply):
    h, w = stdscr.getmaxyx()
    try:
        curses.curs_set(1)
    except Exception:
        pass
    box_w = min(70, w - 4)
    box_h = min(20, h - 4)
    y0 = (h - box_h) // 2
    x0 = (w - box_w) // 2

    # Dim background
    for yy in range(h):
        try:
            stdscr.addstr(yy, 0, " " * w, curses.color_pair(8))
        except Exception:
            pass

    border = curses.color_pair(9)
    top = "╭" + "─" * (box_w - 2) + "╮"
    bot = "╰" + "─" * (box_w - 2) + "╯"
    try:
        stdscr.addstr(y0, x0, top, border)
        stdscr.addstr(y0 + box_h - 1, x0, bot, border)
        for i in range(1, box_h - 1):
            stdscr.addstr(y0 + i, x0, "│", border)
            stdscr.addstr(y0 + i, x0 + box_w - 1, "│", border)
    except Exception:
        pass

    try:
        stdscr.addstr(y0, x0 + 3, " COMMAND PALETTE ",
                      curses.color_pair(4) | curses.A_BOLD)
    except Exception:
        pass

    # Input
    try:
        inp = f" > {query}"
        stdscr.addstr(y0 + 2, x0 + 2, inp[:box_w - 4],
                      curses.color_pair(1) | curses.A_BOLD)
    except Exception:
        pass

    # Results
    start_y = y0 + 4
    for i, (key, label, path) in enumerate(filtered[: box_h - 6]):
        yy = start_y + i
        line = f" {key:<10} {label}"
        if i == sel:
            attr = curses.color_pair(3) | curses.A_BOLD
        else:
            attr = curses.color_pair(10)
        try:
            stdscr.addstr(yy, x0 + 2, line[: box_w - 4].ljust(box_w - 4), attr)
        except Exception:
            pass

    # Footer
    try:
        stdscr.addstr(y0 + box_h - 2, x0 + 2,
                      " ↑↓ select · Enter run · Esc close ",
                      curses.color_pair(8) | curses.A_DIM)
    except Exception:
        pass

    # Position cursor in input
    try:
        cx = x0 + 4 + len(query)
        stdscr.move(y0 + 2, cx)
    except Exception:
        pass

    stdscr.refresh()


def run(stdscr, theme_apply):
    """Interactive palette. Returns (action, path)."""
    query = ""
    sel = 0

    all_cmds = list(COMMANDS) + _plugin_commands()
    while True:
        filtered = [(k, l, p) for k, l, p in all_cmds
                    if not query or _fuzzy_score(query, k + " " + l) > 0]
        filtered.sort(key=lambda x: -_fuzzy_score(query, x[0] + " " + x[1]))
        if sel >= len(filtered):
            sel = max(0, len(filtered) - 1)

        _draw(stdscr, query, sel, filtered, theme_apply)

        ch = stdscr.getch()
        if ch == 27:  # ESC
            return ("cancel", None)
        if ch in (10, 13, curses.KEY_ENTER):
            if not filtered:
                return ("cancel", None)
            key, label, path = filtered[sel]
            return ("run", path)
        if ch in (curses.KEY_UP,):
            sel = (sel - 1) % max(1, len(filtered))
        elif ch in (curses.KEY_DOWN,):
            sel = (sel + 1) % max(1, len(filtered))
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            query = query[:-1]
            sel = 0
        elif 32 <= ch < 127:
            query += chr(ch)
            sel = 0
