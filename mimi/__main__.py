"""Launch Agent Mimi (TUI by default)."""
import sys
from .tui import main as tui_main
from .main import main as classic_main

def main():
    args = sys.argv[1:]
    if "--classic" in args or "-c" in args:
        classic_main()
    else:
        tui_main()

if __name__ == "__main__":
    main()
