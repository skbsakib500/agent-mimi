"""Auto sync on start/exit."""
from .sync import is_repo, pull, push

def on_start():
    """Pull remote changes on startup. Silent if not a repo."""
    if not is_repo():
        return None
    try:
        ok, msg = pull()
        return ("pulled" if ok else "pull-failed", msg)
    except Exception as e:
        return ("error", str(e))

def on_exit():
    """Push local changes on exit. Silent if not a repo."""
    if not is_repo():
        return None
    try:
        ok, msg = push()
        return ("pushed" if ok else "push-failed", msg)
    except Exception as e:
        return ("error", str(e))
