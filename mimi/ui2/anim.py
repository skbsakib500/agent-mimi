"""Nova UI - animations."""
import sys
import time
from . import theme as T

BRAILLE = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
LINE    = "|/-\\"
DOTS    = "⣾⣽⣻⢿⡿⣟⣯⣷"
ARC     = "◜◠◝◞◡◟"
PULSE   = "◐◓◑◒"
MOON    = "🌑🌒🌓🌔🌕🌖🌗🌘"
SQUARE  = "▖▘▝▗"
CLOCK   = "◷◶◵◴"
GROW    = "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"


def _spin(frames, delay=0.08, text="", color_key="primary",
          cycles=1, end="\r"):
    """Generic spinner. Prints on one line, ends with `end`."""
    if not sys.stdout.isatty():
        if text:
            print(text)
        return
    c = T.col(color_key)
    for _ in range(cycles):
        for f in frames:
            sys.stdout.write("\r" + c + f + T.R + " " + text)
            sys.stdout.flush()
            time.sleep(delay)
    sys.stdout.write("\r" + " " * (len(text) + 4) + "\r")
    sys.stdout.flush()


def spinner(text="working", cycles=1, delay=0.08, style="braille"):
    frames = {
        "braille": BRAILLE,
        "line":    LINE,
        "dots":    DOTS,
        "arc":     ARC,
        "pulse":   PULSE,
        "square":  SQUARE,
        "clock":   CLOCK,
    }.get(style, BRAILLE)
    _spin(frames, delay=delay, text=text, cycles=cycles)


def dots(text="thinking", total=3, delay=0.25):
    """Print text then animate 3 dots on one line."""
    if not sys.stdout.isatty():
        print(text + "...")
        return
    sys.stdout.write(text)
    sys.stdout.flush()
    for i in range(total):
        time.sleep(delay)
        sys.stdout.write(".")
        sys.stdout.flush()
    sys.stdout.write("\n")


def typewriter(text, delay=0.02, color_key=None, newline=True):
    """Reveal text character by character."""
    if not sys.stdout.isatty():
        print(text)
        return
    col = T.col(color_key) if color_key else ""
    for ch in text:
        sys.stdout.write(col + ch + (T.R if col else ""))
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
        sys.stdout.write("\n")
        sys.stdout.flush()


def marquee(text, width=40, loops=1, delay=0.05):
    """Scroll text right-to-left inside fixed width."""
    if not sys.stdout.isatty():
        print(text[:width])
        return
    pad = " " * width
    full = pad + text + pad
    for _ in range(loops):
        for i in range(len(full) - width + 1):
            sys.stdout.write("\r" + full[i:i + width])
            sys.stdout.flush()
            time.sleep(delay)
    sys.stdout.write("\r" + " " * width + "\r")


def _lerp(a, b, t):
    return int(a + (b - a) * t)


def shimmer(text, width=40, loops=2, delay=0.04,
            color_a="#4b5563", color_b="#22d3ee"):
    """Sweep a bright highlight across dim text."""
    if not T.has_truecolor() or not sys.stdout.isatty():
        print(text)
        return
    sr, sg, sb = T.hex_rgb(color_a)
    er, eg, eb = T.hex_rgb(color_b)
    n = len(text)
    for l in range(loops):
        for pos in range(-n, n + 1):
            out = []
            for i, ch in enumerate(text):
                dist = abs(i - pos)
                t = max(0.0, 1.0 - dist / 8)
                r = _lerp(sr, er, t)
                g = _lerp(sg, eg, t)
                b = _lerp(sb, eb, t)
                out.append(f"\033[38;2;{r};{g};{b}m{ch}")
            sys.stdout.write("\r" + "".join(out) + T.R)
            sys.stdout.flush()
            time.sleep(delay)
    sys.stdout.write("\n")


def progress_anim(total=30, width=40, delay=0.05, label=""):
    """Animate a progress bar from 0 to 100."""
    if not sys.stdout.isatty():
        print(label + " done")
        return
    for i in range(total + 1):
        pct = i / total * 100
        filled = int(round(width * pct / 100))
        bar = (T.col("success") + "█" * filled + T.R
               + T.col("dim") + "░" * (width - filled) + T.R)
        sys.stdout.write(f"\r  {label} [{bar}] {pct:3.0f}%")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def fade_in(text, steps=8, delay=0.03, color="#22d3ee"):
    """Fade text from black to color."""
    if not T.has_truecolor() or not sys.stdout.isatty():
        print(text)
        return
    r, g, b = T.hex_rgb(color)
    for s in range(steps + 1):
        t = s / steps
        cr = int(r * t)
        cg = int(g * t)
        cb = int(b * t)
        sys.stdout.write(f"\r\033[38;2;{cr};{cg};{cb}m{text}" + T.R)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def reveal_lines(lines, delay=0.06, indent=""):
    """Reveal lines one by one."""
    if not sys.stdout.isatty():
        for ln in lines:
            print(ln)
        return
    for ln in lines:
        print(indent + ln)
        time.sleep(delay)


def pulse_bar(width=40, loops=2, delay=0.08, color_key="accent"):
    """A full bar that pulses in brightness."""
    if not T.has_truecolor() or not sys.stdout.isatty():
        print("█" * width)
        return
    t = T.get()
    r, g, b = T.hex_rgb(t.get(color_key, "#22d3ee"))
    for l in range(loops):
        for s in range(0, 21, 4):
            k = (s / 20.0) if l % 2 == 0 else (1 - s / 20.0)
            cr, cg, cb = int(r * k), int(g * k), int(b * k)
            bar = f"\033[38;2;{cr};{cg};{cb}m" + "█" * width + T.R
            sys.stdout.write("\r  " + bar)
            sys.stdout.flush()
            time.sleep(delay)
    sys.stdout.write("\n")


def boot_sequence(steps=None, delay=0.15):
    """A cinematic boot sequence."""
    steps = steps or [
        ("trust",    "Constitution verified"),
        ("audit",    "Audit chain OK"),
        ("council",  "Loading departments"),
        ("nusrat",   "Waking Nusrat"),
        ("ready",    "Mimi is ready"),
    ]
    from . import widgets as W
    if not sys.stdout.isatty():
        for key, label in steps:
            print(f"  ✓ {label}")
        return
    for key, label in steps:
        sys.stdout.write("\r  ")
        sys.stdout.flush()
        _spin(BRAILLE, delay=0.05, text=label, cycles=1)
        print("  " + T.col("success") + "✓" + T.R + " " + label)
        time.sleep(delay)
    print()


def thinking(duration=1.2, text="Nusrat is thinking"):
    """Thinking animation for a fixed duration."""
    if not sys.stdout.isatty():
        print(text + "...")
        return
    end = time.time() + duration
    i = 0
    while time.time() < end:
        sys.stdout.write("\r  " + T.col("accent")
                         + BRAILLE[i % len(BRAILLE)] + T.R
                         + " " + text + "...")
        sys.stdout.flush()
        i += 1
        time.sleep(0.08)
    sys.stdout.write("\r" + " " * (len(text) + 8) + "\r")
    sys.stdout.flush()
