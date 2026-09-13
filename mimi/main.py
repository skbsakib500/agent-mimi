"""Age    "7": {"title": "APIS", "icon": "[@]", "items": [
        ("API Keys", "mimi.api_manager"),
        ("Gemini", "mimi.api_gemini"),
        ("Groq", "mimi.api_groq"),
        ("Weather", "mimi.api_weather"),
        ("Google Login", "mimi.api_google"),
    ]},
nt Mimi - Command Center."""
from .core import APP_NAME, VERSION, greeting
from .database import fetch_one, table_exists, ensure_schema
from .router import run_module as router_run
from .ui import clock_card
from . import clock
from . import splash
from . import cards
from . import charts
from . import footer
from . import lang
from .motto import get as get_motto, set_text as set_motto
from .ui import (BOLD, BLUE, CYAN, DIM, GRAY, GREEN, MAGENTA, RED, WHITE,
                 YELLOW, c, clear, header, line, menu, mini_bar, mimi,
                 pause, progress_bar, section)

CATEGORIES = {
    "1": {"title": "COMMAND", "icon": "[*]", "items": [
        ("Goals", "mimi.goals"),
        ("Missions", "mimi.missions"),
        ("Tasks", "mimi.tasks")]},
    "2": {"title": "GROWTH", "icon": "[+]", "items": [
        ("Study", "mimi.study"),
        ("Productivity", "mimi.productivity"),
        ("Faith", "mimi.faith"),
        ("Learning", "mimi.learning"),
        ("Career", "mimi.career")]},
    "3": {"title": "FINANCE", "icon": "[$]", "items": [
        ("Finance", "mimi.finance"),
        ("Debts", "mimi.debts")]},
    "4": {"title": "LIFE", "icon": "[~]", "items": [
        ("Daily Life", "mimi.daily"),
        ("Time", "mimi.time"),
        ("Sleep", "mimi.sleep"),
        ("Routines", "mimi.routines"),
        ("Digital", "mimi.digital")]},
    "5": {"title": "MIND", "icon": "[#]", "items": [
        ("Journal", "mimi.journal"),
        ("Relationships", "mimi.relationships"),
        ("Mistakes", "mimi.mistakes"),
        ("Achievements", "mimi.achievements")]},
    "6": {"title": "INTELLIGENCE", "icon": "[i]", "items": [
        ("Analytics", "mimi.analytics"),
        ("Automation", "mimi.automation"),
        ("Intelligence", "mimi.intelligence"),
        ("Insights", "mimi.insights"),
        ("Module Health", "mimi.module_health"),
        ("System Health", "mimi.system_health"),
        ("Export", "mimi.export"),
        ("Report", "mimi.report"),
        ("Progress", "mimi.progress"),
        ("Briefing", "mimi.briefing"),
        ("Suggest", "mimi.suggest"),
        ("Notifications", "mimi.notify_setup"),
        ("Voice", "mimi.speak"),
        ("Backup", "mimi.backup"),
        ("Data Management", "mimi.data_manager"),
        ("Profiles", "mimi.profiles"),
        ("Plugins", "mimi.plugins"),
        ("Cloud Sync", "mimi.sync"),
        ("Web Dashboard", "mimi.web.server")]},
    "7": {"title": "APIS", "icon": "[@]", "items": [
        ("API Keys", "mimi.api_manager"),
        ("Gemini", "mimi.api_gemini"),
        ("Groq", "mimi.api_groq"),
        ("Weather", "mimi.api_weather"),
        ("Google Login", "mimi.api_google")]},

}

def _count(t):
    if not table_exists(t): return 0
    row = fetch_one(f"SELECT COUNT(*) AS n FROM {t}")
    return int(row["n"]) if row else 0

def _val(q, key=None, default=0):
    try:
        row = fetch_one(q)
        if not row: return default
        v = row[key] if key else row[0]
        return default if v is None else v
    except Exception:
        return default

def metrics():
    study_h = _val("SELECT COALESCE(SUM(duration_minutes),0)/60.0 FROM study_sessions WHERE study_date>=date('now','-6 days')")
    income = _val("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='income'")
    expense = _val("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='expense'")
    goal_p = _val("SELECT COALESCE(AVG(progress),0) FROM goals WHERE status='active'")
    miss_p = _val("SELECT COALESCE(AVG(progress),0) FROM missions WHERE status='active'")
    tasks = _count("tasks")
    done = _val("SELECT COUNT(*) FROM tasks WHERE status='completed'")
    study_s = min(100.0, float(study_h) / 7.0 * 100.0)
    task_s = (float(done) / max(1.0, float(tasks)) * 100.0) if tasks else 0.0
    life = round(float(goal_p)*0.35 + float(miss_p)*0.35 + study_s*0.20 + task_s*0.10, 1)
    return {
        "goals": _count("goals"), "missions": _count("missions"), "tasks": tasks,
        "study_hours": float(study_h), "income": float(income),
        "expense": float(expense), "balance": float(income)-float(expense),
        "goal_progress": float(goal_p), "mission_progress": float(miss_p),
        "completed_tasks": int(done), "study_score": study_s, "life_score": life,
    }

def study_week():
    try:
        from .database import fetch_all
        return fetch_all("""SELECT study_date,
                                   COALESCE(SUM(duration_minutes),0) AS minutes
                            FROM study_sessions
                            WHERE study_date >= date('now','-6 days')
                            GROUP BY study_date ORDER BY study_date""")
    except Exception:
        return []

def render_dashboard():
    m = metrics()
    clear()
    header(f"{APP_NAME}  |  COMMAND CENTER", f"v{VERSION}  |  {greeting()}")
    print()
    clock.live(duration=4, width=54)
    print(c(f"  Motto: {get_motto()}", DIM + WHITE))
    print()
    mimi("Type a category number (1-6), Q quick actions, M edit motto.")
    print()
    print(c("  TODAY", BOLD+CYAN))
    print(c("  " + line("-"), GRAY))
    print()
    print("  " + c("+----------------------+", BLUE) + "  " + c("+----------------------+", MAGENTA))
    print("  " + c("| GOAL PROGRESS        |", BLUE) + "  " + c("| MISSION PROGRESS     |", MAGENTA))
    print("  " + c("|", BLUE) + " " + progress_bar(m["goal_progress"], 18, BLUE) + " " + c("|", BLUE)
          + "  " + c("|", MAGENTA) + " " + progress_bar(m["mission_progress"], 18, MAGENTA) + " " + c("|", MAGENTA))
    print("  " + c("+----------------------+", BLUE) + "  " + c("+----------------------+", MAGENTA))
    print()
    print("  " + c("+----------------------+", GREEN) + "  " + c("+----------------------+", CYAN))
    print("  " + c("| STUDY - 7 DAYS       |", GREEN) + "  " + c("| FINANCE              |", CYAN))
    print("  " + c(f"| {m['study_hours']:.1f}h / 7.0h".ljust(22) + "|", GREEN)
          + "  " + c(f"| Balance {m['balance']:,.0f}".ljust(22) + "|", CYAN))
    print("  " + c("+----------------------+", GREEN) + "  " + c("+----------------------+", CYAN))

    section("LIFE SCORE", "[!]")
    sc = m["life_score"]
    color = GREEN if sc >= 70 else YELLOW if sc >= 40 else RED
    print(f"  {c(f'{sc:.1f} / 100', BOLD+color)}")
    print(f"  {progress_bar(sc, 38, color)}")

    section("WEEKLY STUDY", "[^]")
    try:
        lines, _ = charts.weekly_study_bars(days=7, width=36)
        for ln in lines:
            print(ln)
    except Exception as e:
        print(c(f"  chart error: {e}", RED))

    try:
        from . import suggest
        n_sug = len(suggest.analyze())
        if n_sug:
            print(c(f"  💡 {n_sug} suggestion(s) waiting - press 6 > Suggest", YELLOW))
    except Exception:
        pass

    section("SNAPSHOT", "[*]")
    print(f"  Goals {m['goals']}   Missions {m['missions']}   "
          f"Tasks {m['tasks']}   Done {m['completed_tasks']}")
    print(f"  Income {m['income']:,.0f}   Expense {m['expense']:,.0f}   "
          f"Balance {m['balance']:,.0f}")

    section("CATEGORIES", "[/]")
    try:
        from .term import card_w
        if card_w() >= 90:
            cards.show_two_columns(CATEGORIES)
        else:
            cards.show(CATEGORIES)
    except Exception:
        cards.show(CATEGORIES)
    print()
    print(c("  D", CYAN) + " Dashboard   " + c("Q", YELLOW) + " Quick   "
          + c("T", MAGENTA) + " Talk   " + c("M", GREEN) + " Motto   "
          + c("P", CYAN) + " Pomodoro   " + c("L", YELLOW) + " Lang   "
          + c("0", RED) + " Exit")
    try:
        footer.show()
    except Exception:
        pass

def run_module(path):
    def err(msg):
        print(c(f"\n  X {msg}", RED)); pause()
    router_run(path, pause_fn=pause, error_fn=err)

def category_menu(key):
    cat = CATEGORIES[key]
    while True:
        clear()
        header(f"{cat['icon']} {cat['title']}",
               f"{len(cat['items'])} connected modules")
        items = [(str(i), n) for i, (n, _) in enumerate(cat["items"], 1)]
        items.append(("0", "<- Back to Command Center"))
        choice = menu(items, f"{cat['icon']} {cat['title']}")
        if choice == "0": return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(cat["items"]):
                run_module(cat["items"][idx][1])
            else:
                print(c("  X Invalid.", RED)); pause()
        except ValueError:
            print(c("  X Enter a number.", RED)); pause()

def quick_actions():
    acts = {
        "1": ("Goals", "mimi.goals"),
        "2": ("Missions", "mimi.missions"),
        "3": ("Tasks", "mimi.tasks"),
        "4": ("Study", "mimi.study"),
        "5": ("Finance", "mimi.finance"),
        "6": ("Analytics", "mimi.analytics"),
        "7": ("Intelligence", "mimi.intelligence"),
        "8": ("Module Health", "mimi.module_health"),
        "9": ("System Health", "mimi.system_health"),
        "c": ("Live Clock", "mimi.clock"),
        "0": ("<- Back", None),
    }
    while True:
        clear()
        header("QUICK ACTIONS", "v1.0.0 | Shortcuts")
        print()
        for k, (label, _) in acts.items():
            print(f"  [{k}] {label}")
        choice = input(c("\n  > Select: ", BOLD+WHITE)).strip()
        if choice == "0": return
        item = acts.get(choice)
        if not item:
            print(c("  X Invalid.", RED)); pause(); continue
        run_module(item[1])

def edit_motto():
    clear()
    header("EDIT MOTTO", "Single line, shown on dashboard")
    print(f"  Current: {get_motto()}")
    new = input(c("\n  New motto (blank = cancel): ", BOLD+WHITE)).strip()
    if new:
        set_motto(new)
        print(c("  OK Updated.", GREEN))
    pause()


def main():
    try:
        from .core import USER_NAME as _u
        splash.show(_u)
    except Exception:
        pass

    try:
        ensure_schema()
    except Exception as exc:
        print(c(f"  ! Schema bootstrap warning: {exc}", RED)); pause()

    while True:
        render_dashboard()
        choice = input(c("\n  > Command: ", BOLD+WHITE)).strip().lower()
        if choice == "0":
            clear()
            print(c(f"\n  {APP_NAME}", BOLD+MAGENTA))
            mimi("Session closed. Your data is intact.")
            print()
            break
        if choice == "d": continue
        if choice in ("q", "quick"):
            quick_actions(); continue
        if choice in CATEGORIES:
            category_menu(choice); continue
        if choice == "t":
            run_module("mimi.agent"); continue
        if choice == "m":
            edit_motto(); continue
        if choice == "p":
            run_module("mimi.pomodoro"); continue
        if choice == "s":
            run_module("mimi.speak"); continue
        if choice == "l":
            new = lang.toggle()
            msg = "Language set to Bangla" if new == "bn" else "Language set to English"
            print(c(f"  {msg}", CYAN))
            pause(); continue
        print(c("  X Invalid. Use 1-6, D, Q, T, or 0.", RED)); pause()

if __name__ == "__main__":
    main()
