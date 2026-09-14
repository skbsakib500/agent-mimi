"""Launch Agent Mimi (TUI by default)."""
import sys
from .tui import main as tui_main
from .main import main as classic_main

def main():
    from .trust.loader import ensure_trusted
    ensure_trusted(fail_closed=True)
    args = sys.argv[1:]
    if args and args[0] == "sonic":
        from .sonic import main as sonic_main
        import sys as _sys
        _sys.argv = ["sonic"] + args[1:]
        raise SystemExit(sonic_main())
    if "--classic" in args or "-c" in args:
        classic_main()
    else:
        tui_main()

if __name__ == "__main__":
    main()
