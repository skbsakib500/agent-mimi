"""Example plugin."""
PLUGIN_NAME = "Hello"
PLUGIN_DESCRIPTION = "Says hello and counts records"
PLUGIN_VERSION = "1.0"


def main():
    from mimi.ui import GREEN, c, clear, header, pause, section
    from mimi.database import fetch_one

    clear()
    header("👋 HELLO PLUGIN", "Running from mimi/plug_store/hello.py")

    def n(q):
        try:
            r = fetch_one(q)
            return r[0] if r else 0
        except Exception:
            return 0

    section("YOUR DATA", "📊")
    print(f"  Goals     : {n('SELECT COUNT(*) FROM goals')}")
    print(f"  Tasks     : {n('SELECT COUNT(*) FROM tasks')}")
    print(f"  Study     : {n('SELECT COUNT(*) FROM study_sessions')}")
    print()
    print(c("  Plugins work.", GREEN))
    pause()


run = main
