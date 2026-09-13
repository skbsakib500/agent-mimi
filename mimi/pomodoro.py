"""Pomodoro Pro - phased focus timer."""
import time, os, sys, termios, tty, select
from datetime import date

USE = os.environ.get("MIMI_NO_COLOR") != "1"
R="\033[0m"; B="\033[1m"; D="\033[2m"
CY="\033[96m"; BL="\033[94m"; GR="\033[92m"
YL="\033[93m"; RD="\033[91m"; MG="\033[95m"; WH="\033[97m"

def c(t, *codes):
    if not USE: return str(t)
    return "".join(codes) + str(t) + R


PHASES = {
    "work":   ("FOCUS",    25*60, RD),
    "short":  ("SHORT BREAK", 5*60, GR),
    "long":   ("LONG BREAK", 15*60, CY),
}


def _center(text, width, color=None):
    pad = max(0, (width - len(text)) // 2)
    body = (" " * pad) + text + (" " * (width - pad - len(text)))
    return c(body, *(color or []))


def _bar(pct, width, color):
    filled = int(round(width * pct / 100))
    return c("█" * filled, color) + c("░" * (width - filled), D + WH)


def _big_time(seconds):
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"


def _clock_face(seconds, total, color):
    """Bracket-based progress ring."""
    pct = 100 * (1 - seconds / total) if total else 0
    filled = int(round(20 * pct / 100))
    ring = c("●" * filled, color) + c("○" * (20 - filled), D + WH)
    return ring


def _key():
    r, _, _ = select.select([sys.stdin], [], [], 0)
    return sys.stdin.read(1) if r else None


def _render(phase_key, remaining, total, session, done_today):
    title, _, color = PHASES[phase_key]
    W = 52
    pct = 100 * (1 - remaining / total) if total else 100
    lines = []
    lines.append("")
    lines.append(c("  ╭" + "─" * W + "╮", color))
    lines.append(c("  │", color) + _center("", W) + c("│", color))
    lines.append(c("  │", color) + _center(title, W, [B, color]) + c("│", color))
    lines.append(c("  │", color) + _center("", W) + c("│", color))
    lines.append(c("  │", color) + _center(_big_time(remaining), W, [B, WH]) + c("│", color))
    lines.append(c("  │", color) + _center("", W) + c("│", color))
    lines.append(c("  │", color) + _center(_clock_face(remaining, total, color), W) + c("│", color))
    lines.append(c("  │", color) + _center("", W) + c("│", color))
    lines.append(c("  │", color) + " " + _bar(pct, W - 2, color) + " " + c("│", color))
    lines.append(c("  │", color) + _center(f"{pct:.0f}%  •  Session {session}  •  Today {done_today}",
                                              W, [D, WH]) + c("│", color))
    lines.append(c("  │", color) + _center("", W) + c("│", color))
    lines.append(c("  │", color) + _center("[P] Pause   [S] Skip   [Q] Quit", W, [D, WH]) + c("│", color))
    lines.append(c("  │", color) + _center("", W) + c("│", color))
    lines.append(c("  ╰" + "─" * W + "╯", color))
    lines.append("")
    return lines


def _sessions_today():
    try:
        from .database import fetch_one
        r = fetch_one("""SELECT COUNT(*) FROM study_sessions
                         WHERE notes='pomodoro' AND study_date=?""",
                      (str(date.today()),))
        return int(r[0]) if r else 0
    except Exception:
        return 0


def _log(minutes, subject):
    try:
        from .database import execute
        execute("""INSERT INTO study_sessions
                   (subject, study_date, duration_minutes,
                    questions_solved, correct_answers, notes)
                   VALUES (?, ?, ?, 0, 0, 'pomodoro')""",
                (subject, str(date.today()), int(minutes)))
        return True
    except Exception:
        return False


def _run_phase(phase_key, subject):
    """Run one phase with live display. Returns: 'done', 'quit', 'skip'."""
    title, total, color = PHASES[phase_key]
    remaining = total
    paused = False
    n_lines = 0
    old_term = None
    try:
        fd = sys.stdin.fileno()
        old_term = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    except Exception:
        old_term = None

    try:
        while remaining > 0:
            lines = _render(phase_key, remaining, total,
                            session=_sessions_today() + (1 if phase_key == "work" else 0),
                            done_today=_sessions_today())
            if n_lines:
                sys.stdout.write(f"\033[{n_lines}A")
            for ln in lines:
                sys.stdout.write("\033[K" + ln + "\n")
            sys.stdout.flush()
            n_lines = len(lines)

            start = time.time()
            while time.time() - start < 1:
                if old_term:
                    k = _key()
                    if k:
                        lk = k.lower()
                        if lk == "q":
                            return "quit"
                        if lk == "s":
                            return "skip"
                        if lk == "p":
                            paused = not paused
                time.sleep(0.05)
            if not paused:
                remaining -= 1
    finally:
        if old_term:
            try: termios.tcsetattr(fd, termios.TCSADRAIN, old_term)
            except Exception: pass
    return "done"


def _announce(text):
    try:
        from . import notify, speak
        notify.send("Pomodoro", text, priority="high", sound=True, vibrate=True)
        if speak.available():
            speak.speak(text, lang="bn")
    except Exception:
        pass


def run_session(minutes=None, subject="Pomodoro", cycles=4):
    """Full pomodoro cycle: work/short/work/short/work/short/work/long."""
    plan = ["work", "short", "work", "short",
            "work", "short", "work", "long"]
    session_num = 0
    for i, phase in enumerate(plan):
        if phase == "work":
            session_num += 1
        # allow custom work duration
        if phase == "work" and minutes:
            PHASES["work"] = ("FOCUS", int(minutes) * 60, RD)

        result = _run_phase(phase, subject)
        if result == "quit":
            print(c("\n  Quit by user.", YL))
            return
        if result == "done" and phase == "work":
            _log(PHASES["work"][1] // 60, subject)
            try:
                from .award import award
                award("pomodoro")
            except Exception:
                pass
            _announce(f"পোমোডোরো {session_num} শেষ, ব্রেক নিন")
        if result == "done" and phase in ("short", "long"):
            _announce("ব্রেক শেষ, আবার ফোকাস করুন")

    print(c("\n  🎉 Full pomodoro set complete. Excellent work.", GR + B))


def main():
    from .ui import BOLD, CYAN, DIM, GREEN, RED, WHITE, YELLOW
    from .ui import c as uc, clear, header, pause

    clear()
    header("🍅 POMODORO PRO", "Phased focus timer")
    print()
    print("  1. Classic     25 min focus + 5 min break × 4")
    print("  2. Deep work   50 min focus + 10 min break × 3")
    print("  3. Sprint      15 min focus + 3 min break × 5")
    print("  4. Custom")
    print("  0. Back")
    ch = input(uc("\n  > Select: ", BOLD)).strip()

    if ch == "0":
        return
    if ch == "1":
        PHASES["work"]  = ("FOCUS", 25*60, RD)
        PHASES["short"] = ("SHORT BREAK", 5*60, GR)
        PHASES["long"]  = ("LONG BREAK", 15*60, CY)
        cycles = 4
    elif ch == "2":
        PHASES["work"]  = ("DEEP FOCUS", 50*60, RD)
        PHASES["short"] = ("BREAK", 10*60, GR)
        PHASES["long"]  = ("LONG BREAK", 20*60, CY)
        cycles = 3
    elif ch == "3":
        PHASES["work"]  = ("SPRINT", 15*60, RD)
        PHASES["short"] = ("MICRO BREAK", 3*60, GR)
        PHASES["long"]  = ("LONG BREAK", 10*60, CY)
        cycles = 5
    elif ch == "4":
        try:
            m = int(input("  Focus minutes [25]: ").strip() or "25")
            b = int(input("  Break minutes [5]: ").strip() or "5")
        except ValueError:
            print(uc("  X Invalid.", RED)); pause(); return
        PHASES["work"]  = ("FOCUS", m*60, RD)
        PHASES["short"] = ("SHORT BREAK", b*60, GR)
        PHASES["long"]  = ("LONG BREAK", b*3*60, CY)
        cycles = 4
    else:
        return

    subject = input(uc("  Subject [Pomodoro]: ", BOLD)).strip() or "Pomodoro"
    print()
    print(uc(f"  Starting: {PHASES['work'][1]//60} min × {cycles} sessions", DIM + WHITE))
    print(uc("  Controls: [P] Pause  [S] Skip  [Q] Quit", DIM + WHITE))
    time.sleep(1.2)
    run_session(subject=subject, cycles=cycles)
    input(uc("\n  Enter to return...", DIM + WHITE))


run = main
