"""Nova UI - layout engine + flicker-free screen buffer."""
import sys
import shutil
from . import theme as T
from .widgets import cols, visible_len, pad_right


# ─── flicker-free screen buffer ───
class Screen:
    """Double-buffered screen writer. Tracks last frame to avoid redraws."""

    def __init__(self):
        self.last = []

    def clear(self):
        if sys.stdout.isatty():
            sys.stdout.write("\033[2J\033[H")
        else:
            print()
        self.last = []

    def draw(self, lines):
        """Write lines, only redrawing changed rows."""
        cur = list(lines)
        if not sys.stdout.isatty():
            for ln in cur:
                print(ln)
            return
        # If line count shrank, clear extras
        extra = len(self.last) - len(cur)
        for i, ln in enumerate(cur):
            if i < len(self.last) and self.last[i] == ln:
                continue
            sys.stdout.write(f"\033[{i+1};1H\033[2K" + ln)
        for j in range(len(cur), len(cur) + max(0, extra)):
            sys.stdout.write(f"\033[{j+1};1H\033[2K")
        sys.stdout.flush()
        self.last = cur

    def invalidate(self):
        self.last = []


# ─── Stack: vertical composition with gaps ───
class Stack:
    def __init__(self, gap=0):
        self.gap = gap
        self._blocks = []

    def add(self, block):
        """block = list of lines OR str."""
        self._blocks.append(block)
        return self

    def add_lines(self, lines):
        self._blocks.append(list(lines))
        return self

    def render(self):
        out = []
        for i, b in enumerate(self._blocks):
            if isinstance(b, str):
                out.append(b)
            else:
                out.extend(b)
            if self.gap and i < len(self._blocks) - 1:
                out.extend([""] * self.gap)
        return out


# ─── Columns: side-by-side ───
class Columns:
    def __init__(self, gap=2, widths=None):
        self.gap = gap
        self.widths = widths
        self._cols = []

    def add(self, lines):
        self._cols.append(list(lines))
        return self

    def render(self, total_width=None):
        total_width = total_width or cols()
        n = len(self._cols)
        if n == 0:
            return []
        if self.widths:
            w = list(self.widths)
        else:
            each = (total_width - self.gap * (n - 1)) // n
            w = [each] * n
        # pad each block to its width
        padded = []
        for i, block in enumerate(self._cols):
            col_lines = []
            for ln in block:
                if isinstance(ln, str):
                    col_lines.append(pad_right(ln, w[i]))
                else:
                    col_lines.append(pad_right(str(ln), w[i]))
            padded.append(col_lines)
        # interleave
        height = max(len(c) for c in padded)
        sep = " " * self.gap
        out = []
        for r in range(height):
            cells = []
            for i in range(n):
                cells.append(padded[i][r] if r < len(padded[i]) else " " * w[i])
            out.append(sep.join(cells))
        return out


# ─── Grid: 2D cells ───
class Grid:
    """Grid of cells. Add cells row by row."""

    def __init__(self, ncols=2, gap=2, cell_width=None, cell_height=None):
        self.ncols = ncols
        self.gap = gap
        self.cell_width = cell_width
        self.cell_height = cell_height
        self._cells = []       # list of (lines, width_override)

    def add(self, lines, width=None):
        self._cells.append((list(lines), width))
        return self

    def render(self, total_width=None):
        total_width = total_width or cols()
        if not self._cells:
            return []
        n = self.ncols
        # compute col widths
        if self.cell_width:
            cw = [self.cell_width] * n
        else:
            each = (total_width - self.gap * (n - 1)) // n
            cw = [each] * n

        # pad each cell to its width and (optionally) height
        padded = []
        for i, (block, wo) in enumerate(self._cells):
            w = wo or cw[i % n]
            cell = [pad_right(ln if isinstance(ln, str) else str(ln), w)
                    for ln in block]
            if self.cell_height:
                while len(cell) < self.cell_height:
                    cell.append(" " * w)
                cell = cell[: self.cell_height]
            padded.append(cell)

        # pad cells to same height per row
        rows = []
        for i in range(0, len(padded), n):
            row_cells = padded[i:i + n]
            h = max(len(c) for c in row_cells)
            row_cells = [
                c + [" " * (cw[j] if j < len(cw) else 0)
                     for _ in range(h - len(c))] if False else
                c + [" " * len(c[0]) if c else "" for _ in range(h - len(c))]
                for j, c in enumerate(row_cells)
            ]
            rows.append(row_cells)

        # emit
        sep = " " * self.gap
        out = []
        for row_cells in rows:
            h = max(len(c) for c in row_cells)
            for r in range(h):
                cells = []
                for i, c in enumerate(row_cells):
                    line = c[r] if r < len(c) else ""
                    w = len(c[0]) if c else 0
                    cells.append(pad_right(line, w))
                out.append(sep.join(cells))
            # gap between rows
            if self.gap:
                out.append("")
        return out


# ─── Split: header / body / footer ───
class Split:
    """Vertical split: header (fixed) + body (flex) + footer (fixed)."""

    def __init__(self, header=None, body=None, footer=None, gap=1):
        self.header = list(header) if header else []
        self.body = list(body) if body else []
        self.footer = list(footer) if footer else []
        self.gap = gap

    def render(self):
        out = []
        if self.header:
            out.extend(self.header)
        if self.header and self.body:
            out.extend([""] * self.gap)
        out.extend(self.body)
        if self.body and self.footer:
            out.extend([""] * self.gap)
        if self.footer:
            out.extend(self.footer)
        return out


# ─── horizontal split (left panel + right panel) ───
class HSplit:
    def __init__(self, left=None, right=None, gap=2, ratio=0.5):
        self.left = list(left) if left else []
        self.right = list(right) if right else []
        self.gap = gap
        self.ratio = ratio

    def render(self, total_width=None):
        total_width = total_width or cols()
        usable = total_width - self.gap
        lw = int(usable * self.ratio)
        rw = usable - lw
        return Columns(gap=self.gap, widths=[lw, rw]) \
            .add(self.left).add(self.right).render(total_width)


# ─── responsive helpers ───
def responsive(wide, medium, narrow):
    """Pick layout based on terminal width.
    wide: >= 100 cols
    medium: 70-99
    narrow: < 70
    """
    w = cols()
    if w >= 100:
        return wide
    if w >= 70:
        return medium
    return narrow


def wrap(text, width):
    """Word-wrap preserving ANSI codes roughly."""
    words = str(text).split(" ")
    lines = []
    cur = ""
    for w in words:
        if visible_len(cur + " " + w) > width:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip() if cur else w
    if cur:
        lines.append(cur)
    return lines or [""]


def centered(lines, width=None):
    width = width or cols()
    out = []
    for ln in lines:
        pad = max(0, (width - visible_len(ln)) // 2)
        out.append(" " * pad + ln)
    return out


def justified(text, value, width=None, value_color="primary"):
    """Left text, right value, pack to width."""
    width = width or cols()
    left = str(text)
    right = T.c(str(value), T.col(value_color))
    gap = width - visible_len(left) - visible_len(right)
    if gap < 1:
        return left
    return left + " " * gap + right


# ─── responsive helpers ───
def responsive(wide, medium, narrow):
    """Pick layout based on terminal width.
    wide: >= 100 cols
    medium: 70-99
    narrow: < 70
    """
    w = cols()
    if w >= 100:
        return wide
    if w >= 70:
        return medium
    return narrow


def wrap(text, width):
    """Word-wrap preserving ANSI codes roughly."""
    words = str(text).split(" ")
    lines = []
    cur = ""
    for w in words:
        if visible_len(cur + " " + w) > width:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip() if cur else w
    if cur:
        lines.append(cur)
    return lines or [""]


def centered(lines, width=None):
    width = width or cols()
    out = []
    for ln in lines:
        pad = max(0, (width - visible_len(ln)) // 2)
        out.append(" " * pad + ln)
    return out


def justified(text, value, width=None, value_color="primary"):
    """Left text, right value, pack to width."""
    width = width or cols()
    left = str(text)
    right = T.c(str(value), T.col(value_color))
    gap = width - visible_len(left) - visible_len(right)
    if gap < 1:
        return left
    return left + " " * gap + right
