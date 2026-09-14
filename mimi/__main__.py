"""Launch Agent Mimi V11 Nova."""
import sys
from .trust.loader import ensure_trusted

def main():
    ensure_trusted(fail_closed=True)
    args = sys.argv[1:]
    if "--classic" in args or "-c" in args:
        from .main import main as classic
        classic()
    elif args and args[0] == "sonic":
        from .sonic import main as sonic
        sys.argv = ["sonic"] + args[1:]
        raise SystemExit(sonic())
    elif args and args[0] == "ios":
        from .web.server import run_server
        print("\n  iOS app: http://127.0.0.1:8765/app\n")
        run_server(open_browser=True)
    elif args and args[0] == "app":
        from .tui_android import main as android
        android()
    elif args and args[0] == "web":
        from .web.server import run_server
        run_server(open_browser=False)
    else:
        from .tui2 import main as nova
        nova()

if __name__ == "__main__":
    main()
