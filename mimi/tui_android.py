"""Android-style TUI - Material Design inspired."""
import curses
import time
from datetime import datetime, timedelta, timezone

from .core import APP_NAME, VERSION, CODENAME, USER_NAME
from .database import fetch_one, fetch_all

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Dhaka")
except Exception:
    TZ = timezone(timedelta(hours=6))


# ─── Bottom-nav tabs (5 fixed) ───
TABS = [
    ("home",      "⌂",  "Home"),
    ("council",   "♛",  "Council"),
    ("nusrat",    "✦",  "Nusrat"),
    ("stats",     "◉",  "Stats"),
    ("more",      "⋯",  "More"),
]

# ─── Color pairs (Material-ish) ───
CP_TOPBAR   = 1   # white on indigo
CP_TABBAR   = 2   # white on dark grey
CP_TAB_SEL  = 3   # accent on dark
CP_CARD     = 4   # white text on surface
CP_CARD_HL  = 5   # accent text
CP_GOOD     = 6
CP_WARN     = 7
CP_BAD      = 8
CP_DIM      = 9
CP_INDIC    = 10  # tab indicator
CP_ACCENT   = 11


def init_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
    except Exception:
        pass
    pairs = {
        CP_TOPBAR:  (curses.COLOR_WHITE,   curses.COLOR_BLUE),
        CP_TABBAR:  (curses.COLOR_WHITE,   curses.COLOR_BLACK),
        CP_TAB_SEL: (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        CP_CARD:    (curses.COLOR_WHITE,   -1),
        CP_CARD_HL: (curses.COLOR_MAGENTA, -1),
        CP_GOOD:    (curses.COLOR_GREEN,   -1),
        CP_WARN:    (curses.COLOR_YELLOW,  -1),
        CP_BAD:     (curses.COLOR_RED,     -1),
        CP_DIM:     (curses.COLOR_WHITE,   -1),
        CP_INDIC:   (curses.COLOR_MAGENTA, -1),
        CP_ACCENT:  (curses.COLOR_CYAN,    -1),
    }
    for pid, (fg, bg) in pairs.items():
        try:
            curses.init_pair(pid, fg, bg)
        except Exception:
            curses.init_pair(pid, fg, curses.COLOR_BLACK)


def _strip(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\033":
            j = s.find("m", i)
            if j == -1:
                break
            i = j + 1
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def put(stdscr, y, x, text, attr=0, wmax=None):
    plain = _strip(text)
    if wmax:
        plain = plain[:wmax]
    try:
        stdscr.addstr(y, x, plain, attr)
        return len(plain)
    except curses.error:
        return 0


def fill(stdscr, y, x, w, attr=0, ch=" "):
    try:
        stdscr.addstr(y, x, ch * w, attr)
    except curses.error:
        pass


def _q(sql, d=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else d
    except Exception:
        return d


def data():
    d = {}
    d["goals_a"] = _q("SELECT COUNT(*) FROM goals WHERE status='active'")
    d["goals_p"] = _q("SELECT COALESCE(AVG(progress),0) FROM goals WHERE status='active'")
    d["tasks_p"] = _q("SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')")
    d["tasks_od"] = _q("""SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')
                          AND due_date IS NOT NULL AND due_date < date('now')""")
    d["tasks_c"] = _q("SELECT COUNT(*) FROM tasks WHERE status='completed'")
    d["study_w"] = _q("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
                         FROM study_sessions WHERE study_date >= date('now','-6 days')""")
    d["study_t"] = _q("""SELECT COALESCE(SUM(duration_minutes),0)
                         FROM study_sessions WHERE study_date=date('now')""")
    d["income"] = _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='income'")
    d["expense"] = _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='expense'")
    d["balance"] = float(d["income"]) - float(d["expense"])
    d["debts"] = _q("SELECT COUNT(*) FROM debts WHERE status='active'")
    d["journal"] = _q("SELECT COUNT(*) FROM journal")
    try:
        from .xp import level_info
        lv = level_info()
        d["level"] = lv["level"]
        d["xp"] = lv["xp"]
        d["lvl_pct"] = lv["pct"]
        d["title"] = lv["title"]
    except Exception:
        d["level"] = 1; d["xp"] = 0; d["lvl_pct"] = 0; d["title"] = "-"
    d["life"] = round(
        d["goals_p"] * 0.30 + min(100, d["study_w"]/7*100) * 0.30
        + (d["tasks_c"] / max(1, d["tasks_c"] + d["tasks_p"])) * 100 * 0.15
        + min(100, d["lvl_pct"]) * 0.25, 1)
    return d


def bar(pct, width):
    try:
        pct = max(0.0, min(100.0, float(pct)))
    except Exception:
        pct = 0.0
    f = int(round(width * pct / 100))
    return "█" * f + "░" * (width - f)


def draw_topbar(stdscr, w, d, title="MIMI"):
    # Row 0: App bar
    now = datetime.now(TZ)
    fill(stdscr, 0, 0, w, curses.color_pair(CP_TOPBAR))
    left = f"  ☰  {title}"
    put(stdscr, 0, 0, left, curses.color_pair(CP_TOPBAR) | curses.A_BOLD)
    right = f"{now.strftime('%H:%M:%S')}  ⋮  "
    put(stdscr, 0, max(1, w - len(right) - 1), right,
        curses.color_pair(CP_TOPBAR) | curses.A_BOLD)

    # Row 1: greeting + life score
    fill(stdscr, 1, 0, w, curses.color_pair(CP_TOPBAR))
    g = f"  Hi, {USER_NAME}"
    put(stdscr, 1, 0, g[: w // 2], curses.color_pair(CP_TOPBAR))
    life = d["life"]
    ls = f"Life {life:.0f}  ·  Lv{d['level']}  "
    put(stdscr, 1, max(1, w - len(ls) - 1), ls,
        curses.color_pair(CP_TOPBAR) | curses.A_BOLD)

    # Row 2: thin indicator line
    fill(stdscr, 2, 0, w, curses.color_pair(CP_INDIC), "─")


def draw_bottomnav(stdscr, h, w, tab_idx):
    y0 = h - 2
    # separator
    fill(stdscr, y0 - 1, 0, w, curses.color_pair(CP_DIM), "─")

    n = len(TABS)
    # Fixed cell widths
    cw = max(6, w // n)
    total = cw * n
    off = (w - total) // 2

    fill(stdscr, y0, 0, w, curses.color_pair(CP_TABBAR))

    for i, (key, icon, label) in enumerate(TABS):
        x = off + i * cw
        is_sel = (i == tab_idx)

        # icon line
        ic = f" {icon} "
        icp = x + (cw - len(ic)) // 2
        attr = (curses.color_pair(CP_TAB_SEL) | curses.A_BOLD
                if is_sel else curses.color_pair(CP_TABBAR))
        put(stdscr, y0, icp, ic, attr)

        # label line — small
        lp = x + (cw - len(label)) // 2
        lattr = (curses.color_pair(CP_TAB_SEL) | curses.A_BOLD
                 if is_sel else curses.color_pair(CP_TABBAR))
        put(stdscr, y0, lp, label[:cw], lattr)

        # indicator (a small dash above the selected tab)
        if is_sel:
            ind = "━" * min(cw - 2, 4)
            ix = x + (cw - len(ind)) // 2
            put(stdscr, y0 - 1, ix, ind,
                curses.color_pair(CP_INDIC) | curses.A_BOLD)


def draw_card(stdscr, y, x, w, h, title=None, value=None, pct=None,
              sub=None, color_pair=CP_ACCENT):
    """Material-style rounded card."""
    bc = curses.color_pair(CP_DIM)
    # top/bottom
    try:
        stdscr.addstr(y, x, "╭" + "─" * (w - 2) + "╮", bc)
        stdscr.addstr(y + h - 1, x, "╰" + "─" * (w - 2) + "╯", bc)
        for i in range(1, h - 1):
            stdscr.addstr(y + i, x, "│", bc)
            stdscr.addstr(y + i, x + w - 1, "│", bc)
    except curses.error:
        pass
    inner = w - 4
    # title
    if title:
        put(stdscr, y + 1, x + 2, title.upper()[:inner],
            curses.color_pair(CP_DIM) | curses.A_BOLD)
    # value
    if value is not None:
        put(stdscr, y + 2, x + 2, str(value)[:inner],
            curses.color_pair(color_pair) | curses.A_BOLD)
    # bar
    if pct is not None:
        b = bar(pct, max(4, inner))
        put(stdscr, y + 3, x + 2, b[:inner], curses.color_pair(CP_GOOD))
    # sub
    if sub:
        put(stdscr, y + 4, x + 2, str(sub)[:inner],
            curses.color_pair(CP_DIM))


def draw_fab(stdscr, h, w, label="+"):
    """Floating action button - bottom-right, above tab bar."""
    y = h - 4
    x = w - 6
    try:
        stdscr.addstr(y, x, "╭──╮", curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.addstr(y + 1, x, f"│{label} │",
                      curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.addstr(y + 2, x, "╰──╯", curses.color_pair(CP_ACCENT) | curses.A_BOLD)
    except curses.error:
        pass


def screen_home(stdscr, y, x, w, h, d):
    # Big hero card
    hero_w = min(w, 46)
    draw_card(stdscr, y, x, hero_w, 6,
              title="Life Score",
              value=f"{d['life']:.1f} / 100",
              pct=d["life"],
              sub=f"Lv{d['level']} · {d['title']} · {d['xp']} XP",
              color_pair=CP_CARD_HL)
    # Two mini cards below
    cw = (hero_w - 2) // 2
    cy = y + 6
    draw_card(stdscr, cy, x, cw, 6,
              title="Tasks", value=str(d["tasks_p"]),
              sub=f"{d['tasks_od']} overdue",
              color_pair=CP_WARN if d["tasks_od"] else CP_GOOD)
    draw_card(stdscr, cy, x + cw + 2, cw, 6,
              title="Study 7d", value=f"{d['study_w']:.1f}h",
              pct=min(100, d["study_w"]/7*100),
              sub=f"today {d['study_t']}m")
    # Third mini row
    cy2 = cy + 6
    draw_card(stdscr, cy2, x, cw, 6,
              title="Balance", value=f"{d['balance']:,.0f}",
              sub=f"in {d['income']:,.0f} / out {d['expense']:,.0f}",
              color_pair=CP_GOOD if d["balance"] >= 0 else CP_BAD)
    draw_card(stdscr, cy2, x + cw + 2, cw, 6,
              title="Journal", value=str(d["journal"]),
              sub="entries")


def screen_council(stdscr, y, x, w, h, d):
    put(stdscr, y, x + 2, "COUNCIL OF BRAINS",
        curses.color_pair(CP_CARD_HL) | curses.A_BOLD)
    put(stdscr, y + 1, x + 2, "Chairwoman: NUSRAT",
        curses.color_pair(CP_ACCENT))
    try:
        from .council.bootstrap import bootstrap
        bootstrap()
        from .council.council import council
        depts = council().all()
    except Exception as e:
        put(stdscr, y + 3, x + 2, f"error: {e}", curses.color_pair(CP_BAD))
        return
    yy = y + 3
    for dd in depts:
        if yy >= y + h - 1:
            break
        icon = "◈"
        try:
            from .ui2 import icons as I
            icon = I.dept(dd.NAME)
        except Exception:
            pass
        attr = (curses.color_pair(CP_GOOD) if dd.PRIORITY <= 2
                else curses.color_pair(CP_WARN) if dd.PRIORITY <= 5
                else curses.color_pair(CP_DIM))
        put(stdscr, yy, x + 2, f"{icon}  {dd.NAME:<12}", attr | curses.A_BOLD)
        put(stdscr, yy, x + 18, dd.ROLE[: max(0, w - 20)],
            curses.color_pair(CP_DIM))
        yy += 1


def screen_nusrat(stdscr, y, x, w, h, state):
    put(stdscr, y, x + 2, "NUSRAT · Personal AI",
        curses.color_pair(CP_CARD_HL) | curses.A_BOLD)
    log = state.get("log", [])
    yy = y + 2
    max_h = h - 4
    show = log[-max_h:] if len(log) > max_h else log
    for who, text in show:
        if yy >= y + h - 2:
            break
        if who == "you":
            put(stdscr, yy, x + 2, "you › ",
                curses.color_pair(CP_ACCENT) | curses.A_BOLD)
            prefix_len = 6
            attr = curses.color_pair(CP_DIM)
        else:
            put(stdscr, yy, x + 2, "✦ nusrat › ",
                curses.color_pair(CP_GOOD) | curses.A_BOLD)
            prefix_len = 11
            attr = curses.color_pair(CP_CARD)
        # wrap
        avail = max(10, w - prefix_len - 4)
        first = True
        for para in str(text).splitlines():
            chunk = para
            while chunk:
                piece = chunk[:avail]
                chunk = chunk[avail:]
                put(stdscr, yy, x + 2 + prefix_len, piece, attr)
                yy += 1
                if yy >= y + h - 2:
                    break
                first = False
        if yy < y + h - 2:
            yy += 1
    # hint
    put(stdscr, y + h - 2, x + 2, "[i] type  ·  [c] clear",
        curses.color_pair(CP_DIM))


def screen_stats(stdscr, y, x, w, h, d):
    put(stdscr, y, x + 2, "INSIGHTS",
        curses.color_pair(CP_CARD_HL) | curses.A_BOLD)
    yy = y + 2
    rows = [
        ("Active goals", str(d["goals_a"]), CP_CARD),
        ("Goal progress", f"{d['goals_p']:.0f}%", CP_ACCENT),
        ("Pending tasks", str(d["tasks_p"]), CP_WARN if d["tasks_p"] else CP_GOOD),
        ("Overdue", str(d["tasks_od"]), CP_BAD if d["tasks_od"] else CP_GOOD),
        ("Study (7d)", f"{d['study_w']:.1f}h",
         CP_GOOD if d["study_w"] >= 7 else CP_WARN),
        ("Balance", f"৳{d['balance']:,.0f}",
         CP_GOOD if d["balance"] >= 0 else CP_BAD),
        ("Active debts", str(d["debts"]), CP_WARN if d["debts"] else CP_GOOD),
        ("Journal", str(d["journal"]), CP_CARD),
    ]
    for k, v, ck in rows:
        if yy >= y + h - 1:
            break
        put(stdscr, yy, x + 2, k[:22], curses.color_pair(CP_DIM))
        put(stdscr, yy, x + 26, v[: w - 28],
            curses.color_pair(ck) | curses.A_BOLD)
        yy += 1


MORE_ITEMS = [
    ("Goals",     "mimi.goals"),
    ("Missions",  "mimi.missions"),
    ("Finance",   "mimi.finance"),
    ("Debts",     "mimi.debts"),
    ("Journal",   "mimi.journal"),
    ("Predict",   "mimi.predict"),
    ("Review",    "mimi.ai_review"),
    ("Lab",       "mimi.upgrade.lab"),
    ("Sonar",     "mimi.health.diagnostic"),
    ("Sync",      "mimi.sync"),
    ("Web",       "mimi.web.server"),
    ("Settings",  "mimi.api_manager"),
]


def screen_more(stdscr, y, x, w, h, state):
    put(stdscr, y, x + 2, "MORE",
        curses.color_pair(CP_CARD_HL) | curses.A_BOLD)
    yy = y + 2
    sel = state.get("more_sel", 0)
    for i, (label, path) in enumerate(MORE_ITEMS):
        if yy >= y + h - 1:
            break
        attr = (curses.color_pair(CP_TAB_SEL) | curses.A_BOLD
                if i == sel else curses.color_pair(CP_CARD))
        put(stdscr, yy, x + 2, f"  {label:<14}", attr)
        yy += 1


def draw_card(stdscr, y, x, w, h, title=None, value=None, pct=None,
              sub=None, color_pair=CP_ACCENT):
    """Material-style rounded card."""
    bc = curses.color_pair(CP_DIM)
    # top/bottom
    try:
        stdscr.addstr(y, x, "╭" + "─" * (w - 2) + "╮", bc)
        stdscr.addstr(y + h - 1, x, "╰" + "─" * (w - 2) + "╯", bc)
        for i in range(1, h - 1):
            stdscr.addstr(y + i, x, "│", bc)
            stdscr.addstr(y + i, x + w - 1, "│", bc)
    except curses.error:
        pass
    inner = w - 4
    # title
    if title:
        put(stdscr, y + 1, x + 2, title.upper()[:inner],
            curses.color_pair(CP_DIM) | curses.A_BOLD)
    # value
    if value is not None:
        put(stdscr, y + 2, x + 2, str(value)[:inner],
            curses.color_pair(color_pair) | curses.A_BOLD)
    # bar
    if pct is not None:
        b = bar(pct, max(4, inner))
        put(stdscr, y + 3, x + 2, b[:inner], curses.color_pair(CP_GOOD))
    # sub
    if sub:
        put(stdscr, y + 4, x + 2, str(sub)[:inner],
            curses.color_pair(CP_DIM))


def draw_fab(stdscr, h, w, label="+"):
    """Floating action button - bottom-right, above tab bar."""
    y = h - 4
    x = w - 6
    try:
        stdscr.addstr(y, x, "╭──╮", curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.addstr(y + 1, x, f"│{label} │",
                      curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.addstr(y + 2, x, "╰──╯", curses.color_pair(CP_ACCENT) | curses.A_BOLD)
    except curses.error:
        pass


def _prompt(stdscr, h, w):
    curses.echo()
    curses.curs_set(1)
    try:
        stdscr.addstr(h - 3, 2, "  you › ",
                      curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.clrtoeol()
    except curses.error:
        pass
    try:
        s = stdscr.getstr(h - 3, 9, 200).decode("utf-8", "replace")
    except Exception:
        s = ""
    curses.noecho()
    curses.curs_set(0)
    return s


def _chat(text, state):
    if not text.strip():
        return
    state["log"].append(("you", text))
    try:
        from .council.bootstrap import bootstrap
        bootstrap()
        from .council.nusrat import nusrat
        n = nusrat()
        r = n.listen(text, actor=USER_NAME)
        reply = r.get("text", "(no reply)")
    except Exception as e:
        reply = f"[error: {type(e).__name__}: {e}]"
    for line in str(reply).splitlines():
        state["log"].append(("nusrat", line))


def _launch(path, stdscr):
    curses.def_prog_mode()
    curses.endwin()
    try:
        from .router import run_module
        run_module(path)
    except Exception as e:
        print(f"\n[mimi] {type(e).__name__}: {e}")
        input("Press Enter to return...")
    stdscr.refresh()


def run(stdscr):
    try:
        curses.curs_set(0)
    except Exception:
        pass
    stdscr.nodelay(True)
    stdscr.timeout(200)
    init_colors()

    tab = 0
    state = {"log": [("nusrat", f"Ready, {USER_NAME}.")], "more_sel": 0}
    d = data()
    last = 0.0

    while True:
        try:
            h, w = stdscr.getmaxyx()
        except Exception:
            return
        if h < 18 or w < 50:
            stdscr.erase()
            try:
                stdscr.addstr(0, 0, "Terminal too small (50x18+)")
                stdscr.refresh()
            except Exception:
                pass
            time.sleep(0.2)
            continue

        now = time.time()
        if now - last > 2:
            d = data()
            last = now

        stdscr.erase()
        # Content area: below topbar (3 rows), above bottomnav (3 rows)
        cy0 = 3
        ch_ = h - 6
        cx0 = 2
        cw_ = w - 4
        draw_topbar(stdscr, w, d, title=f"{APP_NAME}")
        # dispatch
        name = TABS[tab][0]
        if name == "home":
            screen_home(stdscr, cy0, cx0, cw_, ch_, d)
            draw_fab(stdscr, h, w, "+")
        elif name == "council":
            screen_council(stdscr, cy0, cx0, cw_, ch_, d)
        elif name == "nusrat":
            screen_nusrat(stdscr, cy0, cx0, cw_, ch_, state)
        elif name == "stats":
            screen_stats(stdscr, cy0, cx0, cw_, ch_, d)
        elif name == "more":
            screen_more(stdscr, cy0, cx0, cw_, ch_, state)

        draw_bottomnav(stdscr, h, w, tab)
        stdscr.refresh()

        try:
            ch = stdscr.getch()
        except Exception:
            ch = -1

        if ch in (ord('q'), ord('Q')):
            return
        elif ch in (curses.KEY_LEFT, ord('h')):
            tab = (tab - 1) % len(TABS)
        elif ch in (curses.KEY_RIGHT, ord('l')):
            tab = (tab + 1) % len(TABS)
        elif ch == curses.KEY_UP:
            if TABS[tab][0] == "more":
                state["more_sel"] = (state["more_sel"] - 1) % len(MORE_ITEMS)
        elif ch == curses.KEY_DOWN:
            if TABS[tab][0] == "more":
                state["more_sel"] = (state["more_sel"] + 1) % len(MORE_ITEMS)
        elif ch == ord('r'):
            d = data()
        elif ch == ord('i'):
            txt = _prompt(stdscr, h, w)
            if txt:
                _chat(txt, state)
                d = data()
        elif ch == ord('c'):
            if TABS[tab][0] == "nusrat":
                state["log"] = [("nusrat", "Cleared.")]
        elif ch == ord('1'):
            tab = 0
        elif ch == ord('2'):
            tab = 1
        elif ch == ord('3'):
            tab = 2
        elif ch == ord('4'):
            tab = 3
        elif ch == ord('5'):
            tab = 4
        elif ch in (10, 13, curses.KEY_ENTER):
            name = TABS[tab][0]
            if name == "more":
                path = MORE_ITEMS[state["more_sel"]][1]
                _launch(path, stdscr)
                curses.curs_set(0)
                stdscr.nodelay(True)
                stdscr.timeout(200)
                d = data()
            elif name == "nusrat":
                txt = _prompt(stdscr, h, w)
                if txt:
                    _chat(txt, state)
            elif name == "home":
                # open quick add
                txt = _prompt(stdscr, h, w)
                if txt:
                    _chat(txt, state)


def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass
    print("\n  Mimi app closed.")


if __name__ == "__main__":
    main()
