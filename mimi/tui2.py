"""Nova TUI - premium dashboard for Agent Mimi V11."""
import curses
import time
import sys
from datetime import datetime, timedelta, timezone

from .core import APP_NAME, VERSION, CODENAME, USER_NAME
from .database import fetch_one, fetch_all
from .xp import level_info

from .ui2 import theme as T
from .ui2 import icons as I
from .ui2 import widgets as W
from .ui2 import anim as A
from .ui2 import layout as L

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Dhaka")
except Exception:
    TZ = timezone(timedelta(hours=6))


# ─── nav ───
NAV = [
    ("Dashboard", I.screen("Dashboard")),
    ("Council",   I.screen("Council")),
    ("Nusrat",    I.screen("Mimi")),
    ("Goals",     I.screen("Goals")),
    ("Tasks",     I.screen("Tasks")),
    ("Study",     I.screen("Study")),
    ("Finance",   I.screen("Finance")),
    ("Journal",   I.screen("Journal")),
    ("Progress",  I.STAR),
    ("Health",    I.HEART),
    ("AI Chat",   "✦"),
    ("Modes",     "🎭"),
    ("Learn",     "🧠"),
    ("Telegram",  "📨"),
    ("Location",  "📍"),
    ("Predict",   I.screen("Predict")),
    ("Review",    I.screen("Review")),
    ("Lab",       I.screen("Lab")),
    ("Sonar",     I.screen("Sonar")),
    ("Sync",      I.screen("Sync")),
    ("Web",       I.screen("Web")),
    ("Settings",  I.screen("Settings")),
]


# ─── curses color pairs ───
CP_DEFAULT = 0
CP_HEADER  = 1
CP_SEL     = 2
CP_ACCENT  = 3
CP_GOOD    = 4
CP_WARN    = 5
CP_BAD     = 6
CP_DIM     = 7
CP_BORDER  = 8
CP_TEXT    = 9


def _init_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
    except Exception:
        pass
    pairs = {
        CP_HEADER: (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        CP_SEL:    (curses.COLOR_BLACK,   curses.COLOR_MAGENTA),
        CP_ACCENT: (curses.COLOR_MAGENTA, -1),
        CP_GOOD:   (curses.COLOR_GREEN,   -1),
        CP_WARN:   (curses.COLOR_YELLOW,  -1),
        CP_BAD:    (curses.COLOR_RED,     -1),
        CP_DIM:    (curses.COLOR_WHITE,   -1),
        CP_BORDER: (curses.COLOR_CYAN,    -1),
        CP_TEXT:   (curses.COLOR_WHITE,   -1),
    }
    for pid, (fg, bg) in pairs.items():
        try:
            curses.init_pair(pid, fg, bg)
        except Exception:
            curses.init_pair(pid, fg, curses.COLOR_BLACK)


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


def _rows(sql, limit=10):
    try:
        return [dict(r) for r in fetch_all(sql)[:limit]]
    except Exception:
        return []


# ─── data snapshot ───
def snapshot():
    d = {
        "goals":     _q("SELECT COUNT(*) FROM goals"),
        "goals_a":   _q("SELECT COUNT(*) FROM goals WHERE status='active'"),
        "goals_p":   _q("SELECT COALESCE(AVG(progress),0) FROM goals WHERE status='active'"),
        "tasks_p":   _q("SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')"),
        "tasks_c":   _q("SELECT COUNT(*) FROM tasks WHERE status='completed'"),
        "tasks_od":  _q("""SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')
                           AND due_date IS NOT NULL AND due_date < date('now')"""),
        "study_w":   _q("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
                           FROM study_sessions WHERE study_date >= date('now','-6 days')"""),
        "study_t":   _q("""SELECT COALESCE(SUM(duration_minutes),0)
                           FROM study_sessions WHERE study_date=date('now')"""),
        "income":    _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='income'"),
        "expense":   _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='expense'"),
        "debts":     _q("SELECT COUNT(*) FROM debts WHERE status='active'"),
        "journal":   _q("SELECT COUNT(*) FROM journal"),
    }
    d["balance"] = float(d["income"]) - float(d["expense"])
    try:
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


def study_week():
    try:
        rows = fetch_all(
            """SELECT study_date, COALESCE(SUM(duration_minutes),0) AS m
               FROM study_sessions WHERE study_date >= date('now','-6 days')
               GROUP BY study_date ORDER BY study_date""")
        return [float(r["m"]) for r in rows]
    except Exception:
        return []


# ─── ANSI → curses safe draw ───
def _strip_ansi(s):
    """Remove ANSI escape codes; return plain text."""
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


def _draw(stdscr, y, x, text, attr=0, max_w=None):
    """Draw text at (y,x), strip ANSI, clip to width."""
    plain = _strip_ansi(text)
    if max_w is not None:
        plain = plain[:max_w]
    try:
        stdscr.addstr(y, x, plain, attr)
        return len(plain)
    except curses.error:
        return 0


def _draw_colored(stdscr, y, x, chunks, max_w=None):
    """Draw list of (text, attr) chunks. Returns total width drawn."""
    total = 0
    for text, attr in chunks:
        plain = _strip_ansi(text)
        if max_w is not None and total + len(plain) > max_w:
            plain = plain[: max_w - total]
        try:
            stdscr.addstr(y, x + total, plain, attr)
        except curses.error:
            pass
        total += len(plain)
        if max_w is not None and total >= max_w:
            break
    return total


def _bar_text(pct, width):
    """Return plain ASCII bar (curses-safe)."""
    try:
        pct = max(0.0, min(100.0, float(pct)))
    except Exception:
        pct = 0.0
    filled = int(round(width * pct / 100))
    return "█" * filled + "░" * (width - filled)


def _hline(stdscr, y, x, w, ch="─", attr=None):
    if attr is None:
        attr = curses.color_pair(CP_BORDER)
    try:
        stdscr.addstr(y, x, ch * w, attr)
    except curses.error:
        pass


def draw_header(stdscr, w, m):
    now = datetime.now(TZ)
    # row 0: brand + clock
    try:
        stdscr.attron(curses.color_pair(CP_HEADER) | curses.A_BOLD)
        stdscr.addstr(0, 0, " " * w)
        stdscr.attroff(curses.color_pair(CP_HEADER) | curses.A_BOLD)
    except curses.error:
        pass
    brand = f" ◈ {APP_NAME}  ·  {CODENAME}  ·  v{VERSION} "
    _draw(stdscr, 0, 1, brand, curses.color_pair(CP_HEADER) | curses.A_BOLD)
    clock = now.strftime("%H:%M:%S")
    date = now.strftime("%a %d %b")
    right = f"{date}  {clock} "
    _draw(stdscr, 0, max(1, w - len(right) - 1), right,
          curses.color_pair(CP_HEADER) | curses.A_BOLD)

    # row 1: hero greeting + life score
    greet = f"  Welcome back, {USER_NAME}."
    _draw(stdscr, 1, 0, greet, curses.color_pair(CP_TEXT) | curses.A_BOLD)
    life = m["life"]
    attr = (curses.color_pair(CP_GOOD) if life >= 70
            else curses.color_pair(CP_WARN) if life >= 40
            else curses.color_pair(CP_BAD))
    lifeline = f"Life {life:.1f}  ·  Lv{m['level']} {m['title']}  "
    _draw(stdscr, 1, max(1, w - len(lifeline) - 1), lifeline, attr | curses.A_BOLD)

    # row 2: separator
    _hline(stdscr, 2, 0, w, "═", curses.color_pair(CP_BORDER))


SIDEBAR_W = 18


def draw_sidebar(stdscr, h, sel, focus):
    top = 3
    for i, (name, icon) in enumerate(NAV):
        y = top + i
        if y >= h - 2:
            break
        line = f" {icon} {name}"
        line = line[: SIDEBAR_W - 1].ljust(SIDEBAR_W - 1)
        if i == sel:
            attr = curses.color_pair(CP_SEL) | curses.A_BOLD
            if focus:
                attr |= curses.A_REVERSE
        else:
            attr = curses.color_pair(CP_TEXT)
        try:
            stdscr.addstr(y, 0, " " + line, attr)
        except curses.error:
            pass
    # vertical separator
    for y in range(3, h - 1):
        try:
            stdscr.addstr(y, SIDEBAR_W, "│",
                          curses.color_pair(CP_BORDER))
        except curses.error:
            pass


def draw_footer(stdscr, h, w, m):
    _hline(stdscr, h - 2, 0, w, "┄", curses.color_pair(CP_DIM))
    # status line
    trust = "trust ✓"
    audit = "audit ✓"
    pend = "-"
    try:
        from .guardian.audit import verify_chain
        ok, _, n = verify_chain()
        audit = f"audit {'✓' if ok else '✗'} ({n})"
    except Exception:
        pass
    try:
        from .upgrade import proposal as P
        pend = f"upgrade {len(P.pending())}"
    except Exception:
        pass
    left = f"  {trust}   {audit}   {pend}"
    _draw(stdscr, h - 1, 0, left, curses.color_pair(CP_DIM))
    right = "↑↓ nav · Enter open · : palette · T theme · q quit "
    _draw(stdscr, h - 1, max(1, w - len(right) - 1), right,
          curses.color_pair(CP_DIM))


def draw_dashboard(stdscr, y, x, h, w, m):
    # ── TOP ROW: 3 big cards ──
    cw = (w - 2) // 3
    ch = 7

    cards = [
        ("LIFE SCORE", f"{m['life']:.1f} / 100", m["life"], "goal+study+tasks+level"),
        ("LEVEL", f"Lv{m['level']}  {m['title']}", m["lvl_pct"], f"{m['xp']} XP total"),
        ("STUDY · 7 DAYS", f"{m['study_w']:.1f}h / 7.0h",
         min(100, m["study_w"]/7*100), f"today {m['study_t']} min"),
    ]
    for i, (title, value, pct, sub) in enumerate(cards):
        cy = y
        cx = x + i * (cw + 1)
        _card(stdscr, cy, cx, ch, cw, title, value, pct, sub)

    # ── MID ROW: sparkline + task snapshot ──
    my = y + ch + 1
    mw = w - 1

    # left: study sparkline
    lw = (mw * 6) // 10
    _panel_title(stdscr, my, x, "STUDY · LAST 7 DAYS")
    data = study_week()
    if data:
        mx = max(data + [1])
        bar_w = max(2, (lw - 6) // max(1, len(data)))
        for i, v in enumerate(data):
            frac = v / mx if mx else 0
            bh = int(round(frac * 3))
            cx0 = x + 1 + i * bar_w
            for r in range(3):
                ch_used = "█" if (3 - r) <= bh else " "
                attr = curses.color_pair(CP_GOOD) if ch_used == "█" else 0
                try:
                    stdscr.addstr(my + 1 + r, cx0, ch_used * (bar_w - 1), attr)
                except curses.error:
                    pass
        total = f"  total {sum(data)/60:.1f}h  peak {mx/60:.1f}h"
        _draw(stdscr, my + 4, x + 1, total, curses.color_pair(CP_DIM))
    else:
        _draw(stdscr, my + 2, x + 1, "no study logged this week",
              curses.color_pair(CP_DIM))

    # right: task snapshot
    rx = x + lw + 1
    rw = w - lw - 2
    _panel_title(stdscr, my, rx, "TASKS & FINANCE")
    rows = [
        ("Pending",  m["tasks_p"],  CP_WARN if m["tasks_p"] else CP_GOOD),
        ("Overdue",  m["tasks_od"], CP_BAD  if m["tasks_od"] else CP_GOOD),
        ("Done",     m["tasks_c"],  CP_GOOD),
        ("Balance",  f"৳{m['balance']:,.0f}",
         CP_GOOD if m["balance"] >= 0 else CP_BAD),
        ("Debts",    m["debts"],    CP_WARN if m["debts"] else CP_GOOD),
    ]
    for i, (k, v, ck) in enumerate(rows):
        _draw(stdscr, my + 1 + i, rx, f"  {k:<9}", curses.color_pair(CP_DIM))
        _draw(stdscr, my + 1 + i, rx + 11, str(v),
              curses.color_pair(ck) | curses.A_BOLD)

    # ── BOTTOM: council preview ──
    by = my + 6
    _panel_title(stdscr, by, x, "COUNCIL OF 11 BRAINS")
    try:
        from .council.bootstrap import bootstrap
        bootstrap()
        from .council.council import council
        depts = council().all()
        line = "  NUSRAT (chair)  ·  " + "  ".join(
            f"{I.dept(d.NAME)} {d.NAME}" for d in depts[:6])
        _draw(stdscr, by + 1, x, line[:w - 2], curses.color_pair(CP_TEXT))
        line2 = "  " + "  ".join(
            f"{I.dept(d.NAME)} {d.NAME}" for d in depts[6:])
        _draw(stdscr, by + 2, x, line2[:w - 2], curses.color_pair(CP_TEXT))
    except Exception as e:
        _draw(stdscr, by + 1, x, f"  council unavailable ({type(e).__name__})",
              curses.color_pair(CP_DIM))


def _panel_title(stdscr, y, x, title):
    _draw(stdscr, y, x, f"  {title}", curses.color_pair(CP_ACCENT) | curses.A_BOLD)


def _card(stdscr, y, x, h, w, title, value, pct, sub):
    bc = curses.color_pair(CP_BORDER)
    # border
    try:
        stdscr.addstr(y, x, "╭" + "─" * (w - 2) + "╮", bc)
        stdscr.addstr(y + h - 1, x, "╰" + "─" * (w - 2) + "╯", bc)
        for i in range(1, h - 1):
            stdscr.addstr(y + i, x, "│", bc)
            stdscr.addstr(y + i, x + w - 1, "│", bc)
    except curses.error:
        pass
    _draw(stdscr, y + 1, x + 2, title[: w - 4],
          curses.color_pair(CP_DIM) | curses.A_BOLD)
    _draw(stdscr, y + 2, x + 2, str(value)[: w - 4],
          curses.color_pair(CP_ACCENT) | curses.A_BOLD)
    bar = _bar_text(pct, max(4, w - 6))
    _draw(stdscr, y + 3, x + 2, bar[: w - 4],
          curses.color_pair(CP_GOOD))
    _draw(stdscr, y + 4, x + 2, str(sub)[: w - 4],
          curses.color_pair(CP_DIM))


def draw_council(stdscr, y, x, h, w):
    _panel_title(stdscr, y, x, "COUNCIL OF BRAINS")
    try:
        from .council.bootstrap import bootstrap
        bootstrap()
        from .council.council import council
        depts = council().all()
    except Exception as e:
        _draw(stdscr, y + 2, x + 2, f"error: {e}", curses.color_pair(CP_BAD))
        return
    _draw(stdscr, y + 1, x, f"  Chairwoman: NUSRAT  ·  {len(depts)} departments",
          curses.color_pair(CP_ACCENT) | curses.A_BOLD)
    y0 = y + 3
    for i, d in enumerate(depts):
        yy = y0 + i
        if yy >= y + h - 1:
            break
        icon = I.dept(d.NAME)
        pri = f"[{d.PRIORITY}]"
        attr = (curses.color_pair(CP_GOOD) if d.PRIORITY <= 2
                else curses.color_pair(CP_WARN) if d.PRIORITY <= 5
                else curses.color_pair(CP_DIM))
        _draw(stdscr, yy, x + 2, f"{pri} {icon} {d.NAME:<12}",
              attr | curses.A_BOLD)
        _draw(stdscr, yy, x + 22, d.ROLE[: w - 24],
              curses.color_pair(CP_DIM))


def draw_nusrat(stdscr, y, x, h, w, state):
    _panel_title(stdscr, y, x, "NUSRAT · Personal AI")
    lines = state.get("log", [])
    y0 = y + 2
    max_lines = h - 5
    show = lines[-max_lines:] if len(lines) > max_lines else lines
    for i, (who, text) in enumerate(show):
        yy = y0 + i
        if yy >= y + h - 3:
            break
        if who == "you":
            attr = curses.color_pair(CP_ACCENT) | curses.A_BOLD
            prefix = "  you > "
        else:
            attr = curses.color_pair(CP_GOOD) | curses.A_BOLD
            prefix = "  Nusrat: "
        _draw(stdscr, yy, x, prefix, attr)
        # wrap text
        avail = w - len(prefix) - 2
        chunks = []
        for para in str(text).splitlines():
            if not para:
                chunks.append("")
                continue
            while para:
                chunks.append(para[:avail])
                para = para[avail:]
        for j, c in enumerate(chunks):
            yy2 = yy if j == 0 else yy + j
            if yy2 >= y + h - 3:
                break
            _draw(stdscr, yy2, x + len(prefix), c,
                  curses.color_pair(CP_TEXT) if who != "you"
                  else curses.color_pair(CP_TEXT))
    # input hint
    _draw(stdscr, y + h - 2, x + 2,
          "  [i] type message  ·  [c] clear  ·  [s] save log",
          curses.color_pair(CP_DIM))


def draw_main(stdscr, y, x, h, w, sel, m, state):
    name = NAV[sel][0]
    if name == "Dashboard":
        draw_dashboard(stdscr, y, x, h, w, m)
    elif name == "Council":
        draw_council(stdscr, y, x, h, w)
    elif name == "Nusrat":
        draw_nusrat(stdscr, y, x, h, w, state)
    else:
        _panel_title(stdscr, y, x, f"{name.upper()}")
        _draw(stdscr, y + 2, x + 2,
              "Press Enter to open this module.",
              curses.color_pair(CP_DIM))
        _draw(stdscr, y + 3, x + 2,
              "(editor opens in classic UI)",
              curses.color_pair(CP_DIM))


def _chat_with_nusrat(text, state):
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


def _prompt(stdscr, h, w, label="  you > "):
    curses.echo()
    curses.curs_set(1)
    try:
        stdscr.addstr(h - 3, 1, label, curses.color_pair(CP_ACCENT) | curses.A_BOLD)
        stdscr.clrtoeol()
    except curses.error:
        pass
    try:
        s = stdscr.getstr(h - 3, len(label) + 1, 200).decode("utf-8", "replace")
    except Exception:
        s = ""
    curses.noecho()
    curses.curs_set(0)
    return s


def run(stdscr):
    try:
        curses.curs_set(0)
    except Exception:
        pass
    stdscr.nodelay(True)
    stdscr.timeout(200)
    _init_colors()

    sel = 0
    state = {"log": [("nusrat", f"Ready, {USER_NAME}. Ask me anything.")]}
    m = snapshot()
    last = 0.0

    while True:
        try:
            h, w = stdscr.getmaxyx()
        except Exception:
            return
        if h < 16 or w < 60:
            stdscr.erase()
            try:
                stdscr.addstr(0, 0, "Terminal too small (need 60x16+)")
                stdscr.refresh()
            except Exception:
                pass
            time.sleep(0.2)
            continue

        now = time.time()
        if now - last > 2:
            m = snapshot()
            last = now

        stdscr.erase()
        draw_header(stdscr, w, m)
        draw_sidebar(stdscr, h, sel, focus=False)
        draw_main(stdscr, 3, SIDEBAR_W + 1,
                  h - 4, w - SIDEBAR_W - 1, sel, m, state)
        draw_footer(stdscr, h, w, m)
        stdscr.refresh()

        try:
            ch = stdscr.getch()
        except Exception:
            ch = -1

        if ch in (ord('q'), ord('Q')):
            return
        elif ch == curses.KEY_UP:
            sel = (sel - 1) % len(NAV)
        elif ch == curses.KEY_DOWN:
            sel = (sel + 1) % len(NAV)
        elif ch == ord('T'):
            try:
                _init_colors()
                m = snapshot()
            except Exception:
                pass
        elif ch == ord('r'):
            m = snapshot()
        elif ch == ord('i'):
            txt = _prompt(stdscr, h, w)
            if txt:
                _chat_with_nusrat(txt, state)
                m = snapshot()
        elif ch in (10, 13, curses.KEY_ENTER):
            name = NAV[sel][0]
            if name == "Nusrat":
                txt = _prompt(stdscr, h, w)
                if txt:
                    _chat_with_nusrat(txt, state)
            elif name == "Council":
                pass
            else:
                _launch_editor(stdscr, name)
                curses.curs_set(0)
                stdscr.nodelay(True)
                stdscr.timeout(200)
                m = snapshot()


EDITOR_MAP = {
    "Dashboard":  None,
    "Council":    None,
    "Nusrat":     None,
    "Goals":      "mimi.goals",
    "Tasks":      "mimi.tasks",
    "Study":      "mimi.study",
    "Finance":    "mimi.finance",
    "Journal":    "mimi.journal",
    "Progress":   "mimi.progress",
    "Health":     "mimi.council.departments.health",
    "AI Chat":    "mimi.ai_chat_tui",
    "Modes":      "mimi.persona_tui",
    "Learn":      "mimi.learn_tui",
    "Telegram":   "mimi.telegram_bot",
    "Location":   "mimi.location_tui",
    "Predict":    "mimi.predict",
    "Review":     "mimi.ai_review",
    "Lab":        "mimi.upgrade.lab",
    "Sonar":      "mimi.health.diagnostic",
    "Sync":       "mimi.sync",
    "Web":        "mimi.web.server",
    "Settings":   "mimi.api_manager",
}


def _launch_editor(stdscr, name):
    path = EDITOR_MAP.get(name)
    if not path:
        return
    curses.def_prog_mode()
    curses.endwin()
    try:
        from .router import run_module
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
    print("\n  ◈ Nova closed. Data intact.")


if __name__ == "__main__":
    main()
