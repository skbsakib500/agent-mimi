"""Termux notification bridge."""
import shutil, subprocess

def _have(cmd):
    return shutil.which(cmd) is not None

def available():
    return _have("termux-notification")

def send(title, content, priority="default", sound=False, vibrate=False):
    """Send a notification via termux-api. Silent no-op if unavailable."""
    if not available():
        return False
    cmd = ["termux-notification",
           "--title", str(title)[:64],
           "--content", str(content)[:200],
           "--priority", priority]
    if sound:
        cmd.append("--sound")
    if vibrate:
        cmd += ["--vibrate", "300"]
    try:
        subprocess.Popen(cmd,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def toast(text):
    if _have("termux-toast"):
        try:
            subprocess.Popen(["termux-toast", "-g", "top", str(text)[:120]],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except Exception:
            pass

def vibrate(ms=300):
    if _have("termux-vibrate"):
        try:
            subprocess.Popen(["termux-vibrate", "-d", str(int(ms))],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except Exception:
            pass
