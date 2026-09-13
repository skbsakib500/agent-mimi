PLUGIN_NAME = "Today"
PLUGIN_DESCRIPTION = "Show today's date, time, and greeting"
PLUGIN_VERSION = "1.0"


def main():
    from datetime import datetime
    from mimi.ui import GREEN, CYAN, WHITE, BOLD, c, clear, header, pause
    clear()
    header("📅 TODAY", "")
    now = datetime.now()
    print()
    print(f"  {now.strftime('%A, %d %B %Y')}")
    print(f"  {now.strftime('%H:%M:%S')}")
    print()
    print(c("  Make today count.", GREEN + BOLD))
    pause()


run = main
