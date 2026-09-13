"""Agent Mimi - Full-screen TUI (curses)."""
import curses, time, sys
from datetime import datetime, timedelta, timezone
from .core import APP_NAME, VERSION, USER_NAME
from .database import fetch_one, fetch_all
from .xp import level_info
from . import tui_palette
from . import tui_themes
from . import tui_charts
from . import tui_search
from . import tui_modal
from . import auto_sync

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Dhaka")
except Exception:
    TZ = timezone(timedelta(hours=6))

SCREENS = [
    ("Dashboard",  "⌂"),
    ("Goals",      "◈"),
    ("Missions",   "◉"),
    ("Tasks",      "☑"),
    ("Study",      "✎"),
    ("Finance",    "৳"),
    ("Debts",      "⚖"),
    ("Journal",    "✎"),
    ("Insights",   "★"),
    ("Progress",   "✦"),
    ("Automation", "⚙"),
    ("Profiles",   "👥"),
    ("Plugins",    "🧩"),
    ("Sync",       "☁"),
    ("Web",        "🌐"),
    ("Settings",   "⚒"),
]

# Color pair IDs
CP_HEADER   = 1
CP_SIDEBAR  = 2
CP_SEL      = 3
CP_ACCENT   = 4
CP_GOOD     = 5
CP_WARN     = 6
CP_BAD      = 7
CP_DIM      = 8
CP_BORDER   = 9
CP_CARD     = 10


def init_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
    except Exception:
        pass
    # Delegate to active theme
    tui_themes.apply()
    return

def _old_init_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
    except Exception:
        pass
    pairs = {
        CP_HEADER:  (curses.COLOR_WHITE,   curses.COLOR_BLUE),
        CP_SIDEBAR: (curses.COLOR_CYAN,    -1),
        CP_SEL:     (curses.COLOR_BLACK,   curses.COLOR_MAGENTA),
        CP_ACCENT:  (curses.COLOR_MAGENTA, -1),
        CP_GOOD:    (curses.COLOR_GREEN,   -1),
        CP_WARN:    (curses.COLOR_YELLOW,  -1),
        CP_BAD:     (curses.COLOR_RED,     -1),
        CP_DIM:     (curses.COLOR_WHITE,   -1),
        CP_BORDER:  (curses.COLOR_CYAN,    -1),
        CP_CARD:    (curses.COLOR_WHITE,   -1),
    }
    for pid, (fg, bg) in pairs.items():
        try:
            curses.init_pair(pid, fg, bg)
        except Exception:
            curses.init_pair(pid, fg, curses.COLOR_BLACK)


def q(n):
    try:
        r = fetch_one(n)
        return r[0] if r else 0
    except Exception:
        return 0


def stats():
    d = {
        "goals":    q("SELECT COUNT(*) FROM goals"),
        "goals_a":  q("SELECT COUNT(*) FROM goals WHERE status='active'"),
        "goals_p":  q("SELECT COALESCE(AVG(progress),0) FROM goals WHERE status='active'"),
        "missions": q("SELECT COUNT(*) FROM missions"),
        "tasks_p":  q("SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')"),
        "tasks_c":  q("SELECT COUNT(*) FROM tasks WHERE status='completed'"),
        "tasks_od": q("""SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')
                         AND due_date IS NOT NULL AND due_date < date('now')"""),
        "study_w":  q("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
                         FROM study_sessions WHERE study_date >= date('now','-6 days')"""),
        "study_t":  q("""SELECT COALESCE(SUM(duration_minutes),0)
                         FROM study_sessions WHERE study_date=date('now')"""),
        "income":   q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='income'"),
        "expense":  q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='expense'"),
        "debts":    q("SELECT COUNT(*) FROM debts WHERE status='active'"),
        "journal":  q("SELECT COUNT(*) FROM journal"),
    }
    d["balance"] = d["income"] - d["expense"]
    try:
        lv = level_info()
        d["level"] = lv["level"]
        d["xp"] = lv["xp"]
        d["lvl_pct"] = lv["pct"]
        d["title"] = lv["title"]
    except Exception:
        d["level"] = 1; d["xp"] = 0; d["lvl_pct"] = 0; d["title"] = "-"
    score = round(d["goals_p"]*0.35 + d["study_w"]/7*100*0.20
                  + (d["tasks_c"]/max(1, d["tasks_c"]+d["tasks_p"]))*100*0.10
                  + min(100, d["lvl_pct"])*0.35, 1)
    d["life"] = min(100, score)
    return d


def bar(pct, width, good=True):
    pct = max(0, min(100, pct))
    filled = int(round(width * pct / 100))
    return "█" * filled + "░" * (width - filled)


def draw_header(stdscr, w):
    now = datetime.now(TZ)
    t = now.strftime("%H:%M:%S")
    d = now.strftime("%a %d %b")
    left = f" {APP_NAME}  v{VERSION}  "
    right = f" {d}  {t} "
    stdscr.attron(curses.color_pair(CP_HEADER) | curses.A_BOLD)
    stdscr.addstr(0, 0, " " * w)
    stdscr.addstr(0, 0, left[:w])
    if len(right) < w - len(left):
        stdscr.addstr(0, w - len(right), right)
    stdscr.attroff(curses.color_pair(CP_HEADER) | curses.A_BOLD)


def draw_sidebar(stdscr, h, sel, focus):
    width = 18
    for y in range(2, h - 2):
        stdscr.addstr(y, 0, " " * width)
    for i, (name, icon) in enumerate(SCREENS):
        y = 2 + i
        if y >= h - 2:
            break
        line = f" {icon} {name}"
        line = line[:width].ljust(width)
        if i == sel:
            attr = curses.color_pair(CP_SEL) | curses.A_BOLD
            if focus:
                attr |= curses.A_REVERSE
        else:
            attr = curses.color_pair(CP_SIDEBAR)
        try:
            stdscr.addstr(y, 0, line, attr)
        except Exception:
            pass


def draw_box(stdscr, y, x, h, w, title=""):
    attr = curses.color_pair(CP_BORDER)
    top = "╭" + "─" * (w - 2) + "╮"
    bot = "╰" + "─" * (w - 2) + "╯"
    try:
        stdscr.addstr(y, x, top, attr)
        stdscr.addstr(y + h - 1, x, bot, attr)
        for i in range(1, h - 1):
            stdscr.addstr(y + i, x, "│", attr)
            stdscr.addstr(y + i, x + w - 1, "│", attr)
        if title:
            t = f" {title} "
            stdscr.addstr(y, x + 2, t[:w-4], curses.color_pair(CP_ACCENT) | curses.A_BOLD)
    except Exception:
        pass


def screen_dashboard(stdscr, y, x, h, w, d):
    draw_box(stdscr, y, x, h, w, " OVERVIEW ")
    # 2x2 card grid
    cw = (w - 6) // 2
    ch = (h - 5) // 2
    cards = [
        ("LIFE SCORE", f"{d['life']:.1f}/100", d["life"], "goals+study+tasks+level"),
        ("LEVEL", f"Lv{d['level']}  {d['title']}", d["lvl_pct"], f"{d['xp']} XP"),
        ("STUDY 7d", f"{d['study_w']:.1f}h / 7h", d["study_w"]/7*100, f"today {d['study_t']}m"),
        ("FINANCE", f"৳{d['balance']:,.0f}", 100 if d["balance"] >= 0 else 30, f"in {d['income']:,.0f} / out {d['expense']:,.0f}"),
    ]
    for i, (label, val, pct, sub) in enumerate(cards):
        cy = y + 2 + (i // 2) * ch
        cx = x + 2 + (i % 2) * (cw + 2)
        draw_box(stdscr, cy, cx, ch, cw)
        try:
            stdscr.addstr(cy + 1, cx + 2, label, curses.color_pair(CP_ACCENT) | curses.A_BOLD)
            stdscr.addstr(cy + 2, cx + 2, val, curses.color_pair(CP_GOOD) | curses.A_BOLD)
            b = bar(pct, cw - 4)
            stdscr.addstr(cy + 3, cx + 2, b, curses.color_pair(CP_GOOD))
            stdscr.addstr(cy + 4, cx + 2, sub[:cw-3], curses.color_pair(CP_DIM) | curses.A_DIM)
        except Exception:
            pass


def screen_list(stdscr, y, x, h, w, title, cols, rows, bar_col=None):
    draw_box(stdscr, y, x, h, w, f" {title} ")
    if not rows:
        try:
            stdscr.addstr(y + 2, x + 2, "  (empty)", curses.color_pair(CP_DIM) | curses.A_DIM)
        except Exception:
            pass
        return
    hy = y + 1
    cx = x + 2
    for c, cw in cols:
        try:
            stdscr.addstr(hy, cx, c[:cw].ljust(cw),
                          curses.color_pair(CP_ACCENT) | curses.A_BOLD | curses.A_UNDERLINE)
        except Exception:
            pass
        cx += cw + 1
    for i, row in enumerate(rows[: h - 4]):
        ry = y + 2 + i
        cx = x + 2
        for j, (c, cw) in enumerate(cols):
            val = str(row[j])[:cw].ljust(cw)
            attr = curses.color_pair(CP_CARD)
            if j == 0:
                attr |= curses.A_BOLD
            try:
                stdscr.addstr(ry, cx, val, attr)
            except Exception:
                pass
            cx += cw + 1
        if bar_col is not None:
            try:
                v = float(row[bar_col])
                b = bar(v, 12)
                col = CP_GOOD if v >= 60 else CP_WARN if v >= 30 else CP_BAD
                stdscr.addstr(ry, x + w - 15, b, curses.color_pair(col))
            except Exception:
                pass


def screen_goals(stdscr, y, x, h, w):
    try:
        rows = fetch_all("""SELECT id, title, progress, status FROM goals
                            ORDER BY id DESC LIMIT ?""", (h - 5,))
        data = [(r["id"], r["title"][:30], r["progress"], r["status"]) for r in rows]
    except Exception:
        data = []
    screen_list(stdscr, y, x, h, w, "GOALS",
                [("ID", 4), ("TITLE", 30), ("PROG", 5), ("STATUS", 10)],
                data, bar_col=2)


def screen_missions(stdscr, y, x, h, w):
    try:
        rows = fetch_all("""SELECT id, title, progress, status FROM missions
                            ORDER BY id DESC LIMIT ?""", (h - 5,))
        data = [(r["id"], r["title"][:30], r["progress"], r["status"]) for r in rows]
    except Exception:
        data = []
    screen_list(stdscr, y, x, h, w, "MISSIONS",
                [("ID", 4), ("TITLE", 30), ("PROG", 5), ("STATUS", 10)],
                data, bar_col=2)


def screen_tasks(stdscr, y, x, h, w):
    try:
        rows = fetch_all("""SELECT id, title, due_date, status FROM tasks
                            WHERE status IN ('pending','in_progress')
                            ORDER BY COALESCE(due_date,'9999') LIMIT ?""", (h - 5,))
        data = [(r["id"], r["title"][:30], r["due_date"] or "-", r["status"]) for r in rows]
    except Exception:
        data = []
    screen_list(stdscr, y, x, h, w, "TASKS (open)",
                [("ID", 4), ("TITLE", 30), ("DUE", 12), ("STATUS", 10)], data)


def screen_study(stdscr, y, x, h, w):
    draw_box(stdscr, y, x, h, w, " STUDY · 14 DAYS ")
    try:
        tui_charts.draw_study_trend(stdscr, y + 2, x + 2, h - 6, w - 4)
        tui_charts.draw_xp_spark(stdscr, y + h - 3, x + 2, w - 4)
    except Exception as e:
        try:
            stdscr.addstr(y + 2, x + 2, f"chart error: {e}",
                          curses.color_pair(CP_BAD))
        except Exception:
            pass


def screen_finance(stdscr, y, x, h, w, d):
    draw_box(stdscr, y, x, h, w, " FINANCE ")
    try:
        tui_charts.draw_finance_bars(stdscr, y + 2, x + 2, w - 4,
                                      d["income"], d["expense"])
        bal = d["balance"]
        col = CP_GOOD if bal >= 0 else CP_BAD
        stdscr.addstr(y + 4, x + 2, "Balance ", curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.addstr(y + 4, x + 11, f"৳{bal:,.2f}",
                      curses.color_pair(col) | curses.A_BOLD)
    except Exception:
        pass


def screen_debts(stdscr, y, x, h, w):
    try:
        rows = fetch_all("""SELECT person, debt_type,
                            original_amount - paid_amount AS bal
                            FROM debts WHERE status='active' LIMIT ?""", (h - 5,))
        data = [(r["person"][:20], r["debt_type"], f"{r['bal']:,.0f}") for r in rows]
    except Exception:
        data = []
    screen_list(stdscr, y, x, h, w, "ACTIVE DEBTS",
                [("PERSON", 20), ("TYPE", 12), ("REMAINING", 12)], data)


def screen_journal(stdscr, y, x, h, w):
    try:
        rows = fetch_all("""SELECT entry_date, title FROM journal
                            ORDER BY entry_date DESC LIMIT ?""", (h - 5,))
        data = [(r["entry_date"], (r["title"] or "-")[:40]) for r in rows]
    except Exception:
        data = []
    screen_list(stdscr, y, x, h, w, "JOURNAL",
                [("DATE", 12), ("TITLE", 40)], data)


def screen_insights(stdscr, y, x, h, w, d):
    draw_box(stdscr, y, x, h, w, " INSIGHTS ")
    items = [
        ("Overdue tasks",     f"{d['tasks_od']}", CP_BAD if d["tasks_od"] else CP_GOOD),
        ("Pending tasks",     f"{d['tasks_p']}",  CP_WARN if d["tasks_p"] else CP_GOOD),
        ("Active goals",      f"{d['goals_a']}",  CP_DIM),
        ("Active missions",   f"{d['missions']}", CP_DIM),
        ("Study this week",   f"{d['study_w']:.1f}h", CP_GOOD if d["study_w"] >= 7 else CP_WARN),
        ("Active debts",      f"{d['debts']}",    CP_WARN if d["debts"] else CP_GOOD),
    ]
    for i, (k, v, col) in enumerate(items):
        try:
            stdscr.addstr(y + 2 + i, x + 3, k.ljust(20), curses.color_pair(CP_DIM))
            stdscr.addstr(y + 2 + i, x + 25, v, curses.color_pair(col) | curses.A_BOLD)
        except Exception:
            pass


def screen_progress(stdscr, y, x, h, w, d):
    draw_box(stdscr, y, x, h, w, " PROGRESS ")
    try:
        stdscr.addstr(y + 2, x + 3, f"LEVEL {d['level']}  ·  {d['title']}",
                      curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.addstr(y + 3, x + 3, f"{d['xp']} XP total", curses.color_pair(CP_DIM))
        b = bar(d["lvl_pct"], w - 6)
        stdscr.addstr(y + 5, x + 3, b, curses.color_pair(CP_GOOD))
        stdscr.addstr(y + 6, x + 3, f"{d['lvl_pct']:.0f}% to next level",
                      curses.color_pair(CP_DIM) | curses.A_DIM)
    except Exception:
        pass
    try:
        from .badges import unlocked, BADGES
        got = unlocked()
        stdscr.addstr(y + 8, x + 3, f"BADGES  {len(got)}/{len(BADGES)}",
                      curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        for i, (code, icon, label, _) in enumerate(BADGES[: h - 12]):
            mark = icon if code in got else "·"
            col = CP_GOOD if code in got else CP_DIM
            stdscr.addstr(y + 9 + i, x + 3, f"{mark} {label}"[:w-6],
                          curses.color_pair(col))
    except Exception:
        pass


def screen_automation(stdscr, y, x, h, w, d):
    draw_box(stdscr, y, x, h, w, " AUTOMATION ")
    try:
        rows = fetch_all("""SELECT title, priority FROM recommendations
                            ORDER BY id DESC LIMIT ?""", (h - 5,))
    except Exception:
        rows = []
    if not rows:
        try:
            stdscr.addstr(y + 2, x + 3, "No recommendations. All clear.",
                          curses.color_pair(CP_GOOD))
        except Exception:
            pass
    for i, r in enumerate(rows):
        col = CP_BAD if r["priority"] == "critical" else CP_WARN if r["priority"] == "warning" else CP_DIM
        try:
            stdscr.addstr(y + 2 + i, x + 3, f"[{r['priority'].upper()[:4]}]",
                          curses.color_pair(col) | curses.A_BOLD)
            stdscr.addstr(y + 2 + i, x + 12, r["title"][:w-15], curses.color_pair(CP_CARD))
        except Exception:
            pass


def screen_web(stdscr, y, x, h, w):
    draw_box(stdscr, y, x, h, w, " WEB DASHBOARD ")
    lines = [
        "Start a browser dashboard from here.",
        "",
        "URL: http://127.0.0.1:8765/",
        "",
        "Enter to start the server.",
        "Stop with Ctrl+C in terminal.",
    ]
    for i, line in enumerate(lines):
        try:
            stdscr.addstr(y + 2 + i, x + 3, line[: w - 6],
                          curses.color_pair(CP_DIM))
        except Exception:
            pass


def screen_sync(stdscr, y, x, h, w):
    from . import sync as S
    draw_box(stdscr, y, x, h, w, " CLOUD SYNC ")
    st = S.full_status()
    lines = [
        ("git binary",  "OK" if st["git"] else "MISSING",
         CP_GOOD if st["git"] else CP_BAD),
        ("repo",        "initialized" if st["repo"] else "not initialized",
         CP_GOOD if st["repo"] else CP_WARN),
        ("remote",      st["remote"] or "(none)",
         CP_GOOD if st["remote"] else CP_DIM),
        ("changes",     str(st["changes"]),
         CP_WARN if st["changes"] else CP_GOOD),
    ]
    for i, (k, v, col) in enumerate(lines):
        try:
            stdscr.addstr(y + 2 + i, x + 3, k.ljust(14),
                          curses.color_pair(CP_ACCENT))
            stdscr.addstr(y + 2 + i, x + 19, v[: w - 22],
                          curses.color_pair(col) | curses.A_BOLD)
        except Exception:
            pass
    try:
        stdscr.addstr(y + 7, x + 3, "Enter to open menu",
                      curses.color_pair(CP_DIM) | curses.A_DIM)
    except Exception:
        pass


def screen_plugins(stdscr, y, x, h, w):
    from . import plugins as P
    draw_box(stdscr, y, x, h, w, " PLUGINS · mimi/plugins/ ")
    items = P.discover()
    if not items:
        try:
            stdscr.addstr(y + 2, x + 3, "No plugins yet.",
                          curses.color_pair(CP_DIM) | curses.A_DIM)
            stdscr.addstr(y + 4, x + 3, "Drop a .py into mimi/plugins/",
                          curses.color_pair(CP_DIM) | curses.A_DIM)
        except Exception:
            pass
        return
    for i, p in enumerate(items[: h - 4]):
        yy = y + 2 + i * 2
        ok = p.get("runnable")
        col = CP_GOOD if ok else CP_BAD
        mark = "●" if ok else "○"
        try:
            stdscr.addstr(yy, x + 2, f"{mark} {p['name']}  v{p['version']}",
                          curses.color_pair(col) | curses.A_BOLD)
            if p["description"]:
                stdscr.addstr(yy + 1, x + 4, p["description"][: w - 6],
                              curses.color_pair(CP_DIM) | curses.A_DIM)
        except Exception:
            pass


def screen_profiles(stdscr, y, x, h, w):
    from . import profiles as P
    draw_box(stdscr, y, x, h, w, " PROFILES ")
    act = P.active()
    try:
        stdscr.addstr(y + 2, x + 3, f"Active: {act}",
                      curses.color_pair(CP_GOOD) | curses.A_BOLD)
    except Exception:
        pass
    rows = P.list_profiles()
    for i, name in enumerate(rows[: h - 6]):
        yy = y + 4 + i
        marker = "●" if name == act else "○"
        info = P.info(name)
        desc = info.get("description", "")
        line = f"  {marker} {name:<12} {desc}"
        col = CP_GOOD if name == act else CP_DIM
        try:
            stdscr.addstr(yy, x + 2, line[: w - 4], curses.color_pair(col))
        except Exception:
            pass


def screen_settings(stdscr, y, x, h, w, d):
    draw_box(stdscr, y, x, h, w, " SETTINGS ")
    items = [
        f"User        : {USER_NAME}",
        f"Version     : {VERSION}",
        f"Level       : {d['level']} ({d['title']})",
        f"XP          : {d['xp']}",
        f"DB          : data/mimi.db",
        "",
        "Launch classic menu from terminal:",
        "  python -m mimi.main",
    ]
    for i, line in enumerate(items):
        try:
            stdscr.addstr(y + 2 + i, x + 3, line[:w-6], curses.color_pair(CP_DIM))
        except Exception:
            pass


def draw_main(stdscr, y, x, h, w, screen_idx, d):
    name = SCREENS[screen_idx][0]
    if name == "Dashboard":  screen_dashboard(stdscr, y, x, h, w, d)
    elif name == "Goals":    screen_goals(stdscr, y, x, h, w)
    elif name == "Missions": screen_missions(stdscr, y, x, h, w)
    elif name == "Tasks":    screen_tasks(stdscr, y, x, h, w)
    elif name == "Study":    screen_study(stdscr, y, x, h, w)
    elif name == "Finance":  screen_finance(stdscr, y, x, h, w, d)
    elif name == "Debts":    screen_debts(stdscr, y, x, h, w)
    elif name == "Journal":  screen_journal(stdscr, y, x, h, w)
    elif name == "Insights": screen_insights(stdscr, y, x, h, w, d)
    elif name == "Progress": screen_progress(stdscr, y, x, h, w, d)
    elif name == "Automation": screen_automation(stdscr, y, x, h, w, d)
    elif name == "Profiles": screen_profiles(stdscr, y, x, h, w)
    elif name == "Settings": screen_settings(stdscr, y, x, h, w, d)


def draw_footer(stdscr, h, w, msg="", query=""):
    if msg:
        left = f" {msg} "
    elif query:
        left = f" filter: /{query}   ·   Esc clears   ·   q quit "
    else:
        left = " ↑↓ · Enter · v view · / find · : palette · T theme · Y sync · q quit "
    stdscr.attron(curses.color_pair(CP_HEADER))
    try:
        stdscr.addstr(h - 1, 0, " " * w)
        stdscr.addstr(h - 1, 0, left[:w])
    except Exception:
        pass
    stdscr.attroff(curses.color_pair(CP_HEADER))


def run(stdscr):
    # Auto-pull on startup (silent)
    try:
        auto_sync.on_start()
    except Exception:
        pass
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(200)
    try:
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    except Exception:
        pass
    init_colors()

    sel = 0
    d = stats()
    last = 0.0
    query = ""   # active search filter

    while True:
        try:
            h, w = stdscr.getmaxyx()
        except Exception:
            return

        if h < 14 or w < 60:
            stdscr.erase()
            try:
                stdscr.addstr(0, 0, "Terminal too small. Enlarge to at least 60x14.")
                stdscr.refresh()
            except Exception:
                pass
            time.sleep(0.3)
            continue

        now = time.time()
        if now - last > 2:
            d = stats()
            last = now

        stdscr.erase()
        draw_header(stdscr, w)
        draw_sidebar(stdscr, h, sel, focus=False)
        draw_main(stdscr, 2, 20, h - 3, w - 20, sel, d)
        draw_footer(stdscr, h, w, query=query)
        stdscr.refresh()

        try:
            ch = stdscr.getch()
        except Exception:
            ch = -1

        if ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED):
                    if mx < 18 and 2 <= my < 2 + len(SCREENS):
                        sel = my - 2
            except Exception:
                pass
        elif ch in (ord('q'), ord('Q')):
            return
        elif ch == curses.KEY_UP:
            sel = (sel - 1) % len(SCREENS)
        elif ch == curses.KEY_DOWN:
            sel = (sel + 1) % len(SCREENS)
        elif ch in (ord('r'), ord('R')):
            d = stats()
        elif ch == ord(':'):
            curses.curs_set(1)
            action, path = tui_palette.run(stdscr, tui_themes.apply)
            curses.curs_set(0)
            stdscr.nodelay(True)
            stdscr.timeout(200)
            if action == "run" and path:
                if path == "__QUIT__":
                    return
                if path == "__THEME__":
                    tui_themes.cycle()
                    tui_themes.apply()
                elif path and path.startswith("__PLUGIN__:"):
                    plug_name = path.split(":", 1)[1]
                    curses.def_prog_mode()
                    curses.endwin()
                    from .plugins import run_plugin
                    ok, msg = run_plugin(plug_name)
                    if not ok:
                        print(f"\n[plugin] {msg}")
                        input("Enter to return...")
                    stdscr.refresh()
                else:
                    _run_path(path, stdscr)
                    curses.curs_set(0)
                    stdscr.nodelay(True)
                    stdscr.timeout(200)
            d = stats()
        elif ch == ord('Y'):
            # Manual sync (both ways)
            curses.def_prog_mode()
            curses.endwin()
            from .sync import push as _push, pull as _pull
            print("\n  Syncing...")
            ok1, m1 = _pull()
            print(f"  pull: {'OK' if ok1 else 'X'} {m1[:80]}")
            ok2, m2 = _push()
            print(f"  push: {'OK' if ok2 else 'X'} {m2[:80]}")
            input("  Enter to return...")
            stdscr.refresh()
            stdscr.nodelay(True)
            stdscr.timeout(200)
        elif ch == ord('T'):
            tui_themes.cycle()
            tui_themes.apply()
        elif ch == ord('v'):
            name = _current_screen_name(sel)
            fields = _current_row(name)
            if fields:
                curses.curs_set(0)
                tui_modal.show(stdscr, f" {name} · latest ", fields)
                stdscr.nodelay(True)
                stdscr.timeout(200)
            else:
                curses.curs_set(0)
                tui_modal.show(stdscr, f" {name} ", [("Info", "No records yet.")])
                stdscr.nodelay(True)
                stdscr.timeout(200)
        elif ch == ord('/'):
            q = tui_search.prompt(stdscr, query)
            if q is not None:
                query = q
            curses.curs_set(0)
            stdscr.nodelay(True)
            stdscr.timeout(200)
        elif ch == 27:  # ESC clears filter
            query = ""
        elif ch == ord('\n') or ch == curses.KEY_ENTER:
            # Launch classic editor for this screen
            launch_editor(sel, stdscr)
            curses.curs_set(0)
            stdscr.nodelay(True)
            stdscr.timeout(200)
            d = stats()


EDITOR_MAP = {
    "Dashboard":  None,
    "Goals":      "mimi.goals",
    "Missions":   "mimi.missions",
    "Tasks":      "mimi.tasks",
    "Study":      "mimi.study",
    "Finance":    "mimi.finance",
    "Debts":      "mimi.debts",
    "Journal":    "mimi.journal",
    "Insights":   "mimi.intelligence",
    "Progress":   "mimi.progress",
    "Automation": "mimi.automation",
    "Profiles":   "mimi.profiles",
    "Plugins":    "mimi.plugins",
    "Sync":       "mimi.sync",
    "Web":        "mimi.web.server",
    "Settings":   "mimi.api_manager",
}



def _current_row(name):
    """Return a dict of key stats for the selected screen, for modal."""
    try:
        if name == "Goals":
            r = fetch_one("""SELECT id,title,deadline,priority,progress,status
                             FROM goals ORDER BY id DESC LIMIT 1""")
            return [("ID", r["id"]), ("Title", r["title"]),
                    ("Deadline", r["deadline"] or "-"),
                    ("Priority", r["priority"]),
                    ("Progress", f"{r['progress']}%"),
                    ("Status", r["status"])] if r else []
        if name == "Missions":
            r = fetch_one("""SELECT id,title,deadline,priority,progress,status
                             FROM missions ORDER BY id DESC LIMIT 1""")
            return [("ID", r["id"]), ("Title", r["title"]),
                    ("Deadline", r["deadline"] or "-"),
                    ("Priority", r["priority"]),
                    ("Progress", f"{r['progress']}%"),
                    ("Status", r["status"])] if r else []
        if name == "Tasks":
            r = fetch_one("""SELECT id,title,due_date,priority,status
                             FROM tasks ORDER BY id DESC LIMIT 1""")
            return [("ID", r["id"]), ("Title", r["title"]),
                    ("Due", r["due_date"] or "-"),
                    ("Priority", r["priority"]),
                    ("Status", r["status"])] if r else []
        if name == "Journal":
            r = fetch_one("""SELECT id,entry_date,title,content,mood
                             FROM journal ORDER BY id DESC LIMIT 1""")
            return [("ID", r["id"]), ("Date", r["entry_date"]),
                    ("Title", r["title"] or "-"),
                    ("Mood", r["mood"] or "-"),
                    (None, ""), ("Content", r["content"])] if r else []
    except Exception:
        return []
    return []


def _current_screen_name(idx):
    return SCREENS[idx][0]


def _run_path(path, stdscr):
    from .router import run_module
    curses.def_prog_mode()
    curses.endwin()
    try:
        run_module(path)
    except Exception as e:
        print(f"\n[mimi] {type(e).__name__}: {e}")
        input("Press Enter to return...")
    stdscr.refresh()


def launch_editor(idx, stdscr):
    from .router import run_module
    name = SCREENS[idx][0]
    path = EDITOR_MAP.get(name)
    if not path:
        return
    curses.def_prog_mode()
    curses.endwin()
    try:
        run_module(path)
    except Exception as e:
        print(f"\n[mimi] {type(e).__name__}: {e}")
        input("Press Enter to return...")
    stdscr.refresh()


def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass
    print("\n  🤖 Mimi TUI closed.")


if __name__ == "__main__":
    main()
