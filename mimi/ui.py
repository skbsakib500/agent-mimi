import sys
import os
from datetime import datetime
from mimi.tasks import add_task, list_tasks, edit_task, delete_task, complete_task
from mimi.goals import add_goal, list_goals, edit_goal, delete_goal, update_goal_progress

# ANSI Styling Constants
BOLD = "\033[1m"
BLUE = "\033[34m"
CYAN = "\033[36m"
DIM = "\033[2m"
GRAY = "\033[90m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
RED = "\033[31m"
WHITE = "\033[37m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# UI Helper Functions
def c(text, color=""):
    return f"{color}{text}{RESET}"

def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

def header(*args, **kwargs):
    title = args[0] if len(args) > 0 else ""
    subtitle = args[1] if len(args) > 1 else kwargs.get("subtitle", None)
    print("\n" + "="*66)
    if subtitle:
        print(f"  {title}  |  {subtitle}")
    else:
        print(f"  {title}")
    print("="*66)

def print_header(title):
    print("\n" + "+" + "-"*64 + "+")
    print(f"|  * {title:<60} |")
    print("+" + "-"*64 + "+")

def line(*args, **kwargs):
    char = "-"
    length = 66
    for a in args:
        if isinstance(a, str):
            char = a
        elif isinstance(a, int):
            length = a
    if "char" in kwargs and isinstance(kwargs["char"], str):
        char = kwargs["char"]
    if "length" in kwargs and isinstance(kwargs["length"], int):
        length = kwargs["length"]
    return char * length

def section(title):
    print(f"\n--- {title} ---")

def menu(items):
    for k, v in items.items():
        print(f"  {k}  {v}")

def pause():
    input("\n  Press Enter to continue...")

def mimi(msg=""):
    print(f"  ◈ Mimi: {msg}")

def mini_bar(val=0, *args, **kwargs):
    try:
        val = float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        val = 0.0

    length = 10
    color = ""

    for a in args:
        if isinstance(a, int):
            length = a
        elif isinstance(a, str):
            color = a

    if "length" in kwargs and isinstance(kwargs["length"], int):
        length = kwargs["length"]
    if "color" in kwargs and isinstance(kwargs["color"], str):
        color = kwargs["color"]

    pct = max(0.0, min(1.0, val / 100.0 if val > 1.0 else val))
    filled = int(pct * length)
    empty = max(0, length - filled)

    bar_str = "[" + "=" * filled + " " * empty + "]"
    if color:
        bar_str = f"{color}{bar_str}{RESET}"
    return bar_str

def progress_bar(val=0, *args, **kwargs):
    try:
        val = float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        val = 0.0

    length = 20
    color = ""

    for a in args:
        if isinstance(a, int):
            length = a
        elif isinstance(a, str):
            color = a

    if "length" in kwargs and isinstance(kwargs["length"], int):
        length = kwargs["length"]
    if "color" in kwargs and isinstance(kwargs["color"], str):
        color = kwargs["color"]

    pct = max(0, min(100, int(val)))
    filled = int((pct / 100.0) * length)
    empty = max(0, length - filled)

    bar_str = "[" + "=" * filled + " " * empty + "]"
    if color:
        bar_str = f"{color}{bar_str}{RESET}"
    return f"{bar_str} {pct}%"

def clock_card():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n  [ System Time: {now} ]")

# Menu Implementations
def tasks_menu():
    while True:
        print("\n   TASKS MENU")
        print("  " + "-"*62)
        print("   1  Add task")
        print("   2  List tasks")
        print("   3  Edit task")
        print("   4  Delete task")
        print("   5  Sort / Filter tasks")
        print("   6  Complete task")
        print("   0  Exit")
        
        choice = input("\n  > Select: ").strip()
        
        if choice == "1":
            print_header("NEW TASK")
            title = input("  Title: ").strip()
            if not title:
                print("  X Title required.")
                pause()
                continue
            mission_id = input("  Mission ID (0 = none) [0]: ").strip() or "0"
            desc = input("  Description []: ").strip()
            due = input("  Due date [YYYY-MM-DD]: ").strip() or None
            priority = input("  Priority (low/medium/high/critical) [medium]: ").strip() or "medium"
            add_task(title, int(mission_id) if mission_id.isdigit() else 0, desc, due, priority)
            print("  OK Task saved.")
            pause()

        elif choice == "2":
            display_tasks_list()

        elif choice == "3":
            print_header("EDIT TASK")
            tid = input("  Task ID to edit: ").strip()
            if tid.isdigit():
                ntitle = input("  New Title (blank = keep): ").strip()
                npriority = input("  New Priority (blank = keep): ").strip()
                ndue = input("  New Due Date (blank = keep): ").strip()
                edit_task(int(tid), ntitle or None, npriority or None, ndue or None)
                print("  OK Task updated.")
            else:
                print("  X Invalid ID.")
            pause()

        elif choice == "4":
            print_header("DELETE TASK")
            tid = input("  Task ID to delete: ").strip()
            if tid.isdigit():
                confirm = input(f"  Are you sure you want to delete task {tid}? (y/n): ").strip().lower()
                if confirm == 'y':
                    delete_task(int(tid))
                    print("  OK Task deleted.")
            else:
                print("  X Invalid ID.")
            pause()

        elif choice == "5":
            print_header("SORT / FILTER TASKS")
            print("  1. Sort by ID (default)")
            print("  2. Sort by Priority")
            print("  3. Sort by Due Date")
            print("  4. Filter Active only")
            print("  5. Filter Completed only")
            sub = input("  Select option [1]: ").strip() or "1"
            
            if sub == "2":
                display_tasks_list(sort_by="priority")
            elif sub == "3":
                display_tasks_list(sort_by="due_date")
            elif sub == "4":
                display_tasks_list(status_filter="active")
            elif sub == "5":
                display_tasks_list(status_filter="completed")
            else:
                display_tasks_list(sort_by="id")

        elif choice == "6":
            print_header("COMPLETE TASK")
            tid = input("  Task ID to complete: ").strip()
            if tid.isdigit():
                complete_task(int(tid))
                print("  OK Task completed.")
            else:
                print("  X Invalid ID.")
            pause()

        elif choice == "0":
            break
        else:
            print("  X Invalid.")
            pause()

def display_tasks_list(sort_by="id", status_filter=None):
    print_header("TASKS LIST")
    tasks = list_tasks(sort_by=sort_by, status_filter=status_filter)
    if not tasks:
        print("  No tasks found.")
    for t in tasks:
        print(line())
        print(f"  ID: {t[0]}")
        print(f"  Title: {t[1]}")
        print(f"  Priority: {t[2]}")
        print(f"  Status: {t[3]}")
        print(f"  Due Date: {t[4] or 'None'}")
    print(line())
    pause()

def goals_menu():
    while True:
        print("\n   GOALS MENU")
        print("  " + "-"*62)
        print("   1  Add goal")
        print("   2  List goals")
        print("   3  Edit goal")
        print("   4  Delete goal")
        print("   5  Sort goals")
        print("   6  Update progress")
        print("   0  Exit")
        
        choice = input("\n  > Select: ").strip()
        
        if choice == "1":
            print_header("NEW GOAL")
            title = input("  Title: ").strip()
            if not title:
                print("  X Title required.")
                pause()
                continue
            desc = input("  Description []: ").strip()
            deadline = input("  Deadline [YYYY-MM-DD]: ").strip() or None
            priority = input("  Priority (low/medium/high/critical) [medium]: ").strip() or "medium"
            progress = input("  Progress % [0]: ").strip() or "0"
            add_goal(title, desc, deadline, priority, int(progress) if progress.isdigit() else 0)
            print("  OK Goal saved.")
            pause()

        elif choice == "2":
            display_goals_list()

        elif choice == "3":
            print_header("EDIT GOAL")
            gid = input("  Goal ID to edit: ").strip()
            if gid.isdigit():
                ntitle = input("  New Title (blank = keep): ").strip()
                npriority = input("  New Priority (blank = keep): ").strip()
                ndeadline = input("  New Deadline (blank = keep): ").strip()
                edit_goal(int(gid), ntitle or None, npriority or None, ndeadline or None)
                print("  OK Goal updated.")
            else:
                print("  X Invalid ID.")
            pause()

        elif choice == "4":
            print_header("DELETE GOAL")
            gid = input("  Goal ID to delete: ").strip()
            if gid.isdigit():
                confirm = input(f"  Are you sure you want to delete goal {gid}? (y/n): ").strip().lower()
                if confirm == 'y':
                    delete_goal(int(gid))
                    print("  OK Goal deleted.")
            else:
                print("  X Invalid ID.")
            pause()

        elif choice == "5":
            print_header("SORT GOALS")
            print("  1. Sort by ID (default)")
            print("  2. Sort by Priority")
            print("  3. Sort by Progress")
            sub = input("  Select option [1]: ").strip() or "1"
            
            if sub == "2":
                display_goals_list(sort_by="priority")
            elif sub == "3":
                display_goals_list(sort_by="progress")
            else:
                display_goals_list(sort_by="id")

        elif choice == "6":
            print_header("UPDATE GOAL PROGRESS")
            gid = input("  Goal ID: ").strip()
            if gid.isdigit():
                prog = input("  New Progress %: ").strip()
                if prog.isdigit():
                    update_goal_progress(int(gid), int(prog))
                    print("  OK Progress updated.")
            else:
                print("  X Invalid ID.")
            pause()

        elif choice == "0":
            break
        else:
            print("  X Invalid.")
            pause()

def display_goals_list(sort_by="id"):
    print_header("GOALS LIST")
    goals = list_goals(sort_by=sort_by)
    if not goals:
        print("  No goals found.")
    for g in goals:
        print(line())
        print(f"  ID: {g[0]}")
        print(f"  Title: {g[1]}")
        print(f"  Priority: {g[2]}")
        print(f"  Progress %: {g[3]}")
        print(f"  Status: {g[4]}")
        print(f"  Deadline: {g[5] or 'None'}")
    print(line())
    pause()

def main():
    while True:
        print("\n" + "="*25 + " AGENT MIMI CLASSIC " + "="*25)
        print("   1  Goals Menu")
        print("   2  Tasks Menu")
        print("   0  Exit")
        choice = input("\n  > Select: ").strip()
        if choice == "1":
            goals_menu()
        elif choice == "2":
            tasks_menu()
        elif choice == "0":
            print("\n  ◈ Classic closed. Data intact.\n")
            break
        else:
            print("  X Invalid option.")

if __name__ == "__main__":
    main()
