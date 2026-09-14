"""Nova UI - widget library."""
import shutil
from . import theme as T
from . import icons as I
from .theme import c, R, B, D, I as IT, U


def cols(default=78):
    try:
        return max(60, min(shutil.get_terminal_size((default, 24)).columns, 120))
    except Exception:
        return default


def visible_len(s):
    """Length of a string ignoring ANSI escapes."""
    out = 0
    i = 0
    while i < len(s):
        if s[i] == "\033":
            j = s.find("m", i)
            if j == -1:
                break
            i = j + 1
        else:
            out += 1
            i += 1
    return out


def pad_right(s, width):
    pad = max(0, width - visible_len(s))
    return s + " " * pad


def pad_left(s, width):
    pad = max(0, width - visible_len(s))
    return " " * pad + s


def center(s, width):
    ln = visible_len(s)
    if ln >= width:
        return s
    left = (width - ln) // 2
    right = width - ln - left
    return " " * left + s + " " * right


def truncate(s, width, ellipsis="…"):
    if visible_len(s) <= width:
        return s
    # naive: strip only ANSI at end
    plain = s
    if len(plain) <= width:
        return s
    return plain[: max(0, width - 1)] + ellipsis


# ─── gradient text ───
def _lerp(a, b, t):
    return int(a + (b - a) * t)


def gradient(text, start_hex=None, end_hex=None, bold=False):
    """Truecolor horizontal gradient. Falls back to plain text."""
    if not T.has_truecolor():
        if bold:
            return c(text, B)
        return text
    t = T.get()
    s_hx = start_hex or t["primary"]
    e_hx = end_hex or t["accent"]
    sr, sg, sb = T.hex_rgb(s_hx)
    er, eg, eb = T.hex_rgb(e_hx)
    n = max(1, len(text))
    out = []
    if bold:
        out.append(B)
    for i, ch in enumerate(text):
        f = i / (n - 1) if n > 1 else 0
        r = _lerp(sr, er, f)
        g = _lerp(sg, eg, f)
        b = _lerp(sb, eb, f)
        out.append(f"\033[38;2;{r};{g};{b}m{ch}")
    out.append(R)
    return "".join(out)


def divider(char=None, width=None, color_key="border"):
    char = char or I.H_LINE
    width = width or cols()
    return c(char * width, T.col(color_key))


def divider_text(text, char=None, width=None, color_key="border"):
    """Divider with centered text."""
    char = char or I.H_LINE
    width = width or cols()
    if not text:
        return divider(char, width, color_key)
    inner = f" {text} "
    rem = max(0, width - len(inner))
    left = rem // 2
    right = rem - left
    return (c(char * left, T.col(color_key))
            + c(inner, T.col("muted"))
            + c(char * right, T.col(color_key)))


def title_bar(text, width=None, color_key="primary", pad=" "):
    """Colored title bar."""
    width = width or cols()
    body = f"{pad}{text}{pad}"
    return c(body.ljust(width), T.bcol(color_key), B)


# ─── box / panel ───
def box(lines, width=None, title=None, color_key="border",
        title_color="accent", padding=1, rounded=True):
    """Return list of strings, one per line, of a bordered box."""
    width = width or cols()
    if rounded:
        tl, tr, bl, br = I.RBOX_TL, I.RBOX_TR, I.RBOX_BL, I.RBOX_BR
    else:
        tl, tr, bl, br = I.BOX_TL, I.BOX_TR, I.BOX_BL, I.BOX_BR
    h = I.H_LINE
    v = I.BOX_V
    bc = T.col(color_key)
    tc = T.col(title_color)

    inner_w = width - 2
    out = []

    # top border
    if title:
        title_txt = f" {title} "
        top_inner = h * 2 + tc + B + title_txt + R + bc + h * (inner_w - 2 - len(title_txt))
        top_inner = top_inner[:max(0, inner_w)]
        # crude length management; fall back if misaligned
        tlen = len(title_txt)
        top_inner = h * 2 + tc + B + title_txt + R + bc + h * (inner_w - 2 - tlen)
    else:
        top_inner = h * inner_w
    out.append(bc + tl + top_inner + tr + R)

    # top padding
    for _ in range(padding):
        out.append(bc + v + " " * inner_w + v + R)

    # content
    for ln in lines:
        ln = truncate(ln, inner_w - 2 * padding)
        body = " " * padding + pad_right(ln, inner_w - 2 * padding) + " " * padding
        out.append(bc + v + body + v + R)

    # bottom padding
    for _ in range(padding):
        out.append(bc + v + " " * inner_w + v + R)

    # bottom border
    out.append(bc + bl + h * inner_w + br + R)
    return out


def panel(lines, width=None, title=None):
    """Print a box directly."""
    for ln in box(lines, width=width, title=title):
        print(ln)


# ─── sparkline ───
def sparkline(values, color_key="accent"):
    """Return a single-line sparkline using ▁▂▃▄▅▆▇█."""
    chars = I.SPARK_BARS
    if not values:
        return ""
    try:
        vals = [float(v) for v in values]
    except Exception:
        return ""
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    out = []
    for v in vals:
        idx = int((v - mn) / rng * (len(chars) - 1))
        out.append(chars[idx])
    return c("".join(out), T.col(color_key))


# ─── horizontal bar ───
def hbar(pct, width=30, color_key="success", show_pct=True):
    try:
        pct = max(0.0, min(100.0, float(pct)))
    except (TypeError, ValueError):
        pct = 0.0
    filled = int(round(width * pct / 100))
    empty = width - filled
    bar = c(I.BAR_FULL * filled, T.col(color_key)) + c(I.BAR_EMPTY * empty, T.col("dim"))
    if show_pct:
        bar += " " + c(f"{pct:3.0f}%", T.col("muted"))
    return bar


def gradient_bar(pct, width=30, start_hex=None, end_hex=None):
    """A bar with gradient fill."""
    try:
        pct = max(0.0, min(100.0, float(pct)))
    except (TypeError, ValueError):
        pct = 0.0
    filled = int(round(width * pct / 100))
    if not T.has_truecolor():
        return hbar(pct, width)
    t = T.get()
    sr, sg, sb = T.hex_rgb(start_hex or t["success"])
    er, eg, eb = T.hex_rgb(end_hex or t["accent"])
    out = []
    for i in range(width):
        if i < filled:
            f = i / max(1, width - 1)
            r = _lerp(sr, er, f)
            g = _lerp(sg, eg, f)
            b = _lerp(sb, eb, f)
            out.append(f"\033[38;2;{r};{g};{b}m{I.BAR_FULL}")
        else:
            out.append(c(I.BAR_EMPTY, T.col("dim")))
    out.append(R)
    return "".join(out)


def gauge(pct, width=40, color_key=None):
    """Gauge with brackets."""
    try:
        pct = max(0.0, min(100.0, float(pct)))
    except (TypeError, ValueError):
        pct = 0.0
    if color_key is None:
        color_key = ("success" if pct >= 70
                     else "warning" if pct >= 40
                     else "danger")
    inner = hbar(pct, width, color_key, show_pct=False)
    return "[" + inner + "]"


# ─── badge / pill ───
def badge(text, color_key="primary", icon=None):
    """Pill-shaped badge."""
    inner = f" {icon} {text} " if icon else f" {text} "
    return c(inner, T.bcol(color_key), B)


def pill(text, color_key="accent"):
    return "(" + c(text, T.col(color_key)) + ")"


def chip(text, color_key="primary"):
    return "[" + c(text, T.col(color_key) + B) + "]"


# ─── card ───
def card(title, value, subtitle="", pct=None, width=30,
         color_key="primary", spark=None):
    """Return list of lines for a small card."""
    lines = []
    # title
    lines.append(c(title.upper(), T.col("muted") + B))
    # value
    lines.append(c(str(value), T.col(color_key) + B))
    # bar
    if pct is not None:
        lines.append(gradient_bar(pct, width - 6))
    # spark
    if spark:
        lines.append(sparkline(spark, color_key))
    # subtitle
    if subtitle:
        lines.append(c(subtitle, T.col("dim")))
    return box(lines, width=width, padding=1)


# ─── table ───
def table(headers, rows, widths=None, colors=None):
    """Return list of lines for an auto-width table."""
    if not rows:
        return [c("(no rows)", T.col("dim"))]
    n = len(headers)
    if widths is None:
        widths = [max(len(str(headers[i])), max(len(str(r[i])) for r in rows))
                  for i in range(n)]
    sep = c(" │ ", T.col("dim"))
    lines = []
    # header
    head = sep.join(
        c(str(headers[i]).ljust(widths[i]), T.col("primary") + B)
        for i in range(n))
    lines.append(head)
    lines.append(c("─┼─".join("─" * w for w in widths), T.col("dim")))
    # rows
    for row in rows:
        cells = []
        for i in range(n):
            txt = str(row[i])[:widths[i]].ljust(widths[i])
            col_key = colors[i] if colors and i < len(colors) else "text"
            cells.append(c(txt, T.col(col_key)))
        lines.append(sep.join(cells))
    return lines


# ─── tree ───
def tree(node, children=None, prefix="", is_last=True, depth=0):
    """Return list of lines for a nested tree.

    node: str (root label)
    children: list of (node, [children]) pairs
    """
    out = []
    branch = "" if depth == 0 else (I.BOX_BL if is_last else I.BOX_LT)
    connector = "─ " if depth > 0 else ""
    out.append(prefix + c(branch, T.col("dim")) + c(connector, T.col("dim"))
               + str(node))
    if children:
        new_prefix = prefix + ("" if depth == 0 else
                                ("  " if is_last else c(I.BOX_V, T.col("dim")) + " "))
        n = len(children)
        for i, child in enumerate(children):
            last = (i == n - 1)
            if isinstance(child, tuple):
                lbl, sub = child[0], child[1]
            else:
                lbl, sub = child, None
            out.extend(tree(lbl, sub, new_prefix, last, depth + 1))
    return out


# ─── hero banner ───
def hero(title, subtitle="", width=None):
    """Big centered hero section."""
    width = width or cols()
    out = []
    out.append("")
    out.append(center(gradient(title, bold=True), width))
    if subtitle:
        out.append(center(c(subtitle, T.col("muted")), width))
    out.append("")
    return out


# ─── screen header ───
def header(title, subtitle="", width=None, icon=None):
    width = width or cols()
    out = []
    out.append("")
    icon_str = f"{icon} " if icon else ""
    left = c(icon_str + title, T.col("primary") + B)
    right = c(subtitle, T.col("muted")) if subtitle else ""
    # pack
    gap = width - visible_len(left) - visible_len(right) - 2
    if gap < 1:
        out.append(c("  " + title, T.col("primary") + B))
    else:
        out.append("  " + left + " " * gap + right)
    out.append(divider(I.H_LINE, width, "border"))
    return out


# ─── status footer ───
def footer(items, width=None):
    """items = list of (label, value, color_key)."""
    width = width or cols()
    out = []
    out.append(divider(I.H_DOT, width, "dim"))
    parts = []
    for label, value, key in items:
        parts.append(c(f"{label} ", T.col("dim"))
                     + c(str(value), T.col(key) + B))
    # join with dim dots
    joined = c("  ·  ", T.col("dim")).join(parts)
    out.append("  " + joined)
    return out


def section(title, icon=None, width=None):
    width = width or cols()
    label = f"{icon} {title}" if icon else title
    return [c("", T.col("text")),
            c("  " + label, T.col("accent") + B),
            divider(I.H_LINE, width, "dim")]
