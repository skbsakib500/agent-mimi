"""Check Termux API availability + test notification."""
import shutil
from . import notify
from .ui import GREEN, RED, YELLOW, c, clear, header, pause

def check():
    clear()
    header("NOTIFICATIONS", "Termux:API check")
    have_api_cmd = notify.available()
    have_app = shutil.which("termux-toast") is not None
    print()
    print(f"  termux-notification : {'OK' if have_api_cmd else 'MISSING'}")
    print(f"  termux-toast        : {'OK' if have_app else 'MISSING'}")
    print()
    if not have_api_cmd:
        print(c("  To enable:", YELLOW))
        print("    1. Install Termux:API app from F-Droid")
        print("    2. In Termux:  pkg install termux-api")
    else:
        print(c("  Notifications ready.", GREEN))
    print()
    print("  1. Send test notification")
    print("  0. Back")
    ch = input(c("\n  > Select: ")).strip()
    if ch == "1":
        ok = notify.send("Agent Mimi",
                         "Test notification — you're all set.",
                         priority="high", sound=True, vibrate=True)
        if ok:
            print(c("\n  Sent. Check your notification shade.", GREEN))
        else:
            print(c("\n  Failed. Is Termux:API installed?", RED))
        pause()

run = check
