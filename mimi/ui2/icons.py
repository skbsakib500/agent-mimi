"""Nova UI - icon set.

Uses Unicode symbols that work on Termux default fonts.
Nerd Font icons are used when MIMI_NERD=1.
"""
import os

_NERD = os.environ.get("MIMI_NERD") == "1"


def n(nerd_icon, unicode_fallback):
    """Pick Nerd Font icon if enabled, else Unicode."""
    return nerd_icon if _NERD else unicode_fallback


# ─── brand / status ───
LOGO        = "◈"
CROWN       = "♛"
STAR        = "✦"
SPARK       = "✧"
DIAMOND     = "◈"
CIRCLE      = "●"
CIRCLE_O    = "○"
SQUARE      = "■"
TRIANGLE    = "▲"
CHECK       = "✓"
CROSS       = "✗"
WARN        = "⚠"
INFO        = "ℹ"
FIRE        = "🔥"
BOLT        = "⚡"
HEART       = "♥"
SKULL       = "☠"
GHOST       = "◌"

# ─── arrows / nav ───
ARROW_R     = "→"
ARROW_L     = "←"
ARROW_U     = "↑"
ARROW_D     = "↓"
CHEVRON_R   = "›"
CHEVRON_L   = "‹"
BULLET      = "•"
DOT         = "·"
BAR         = "│"

# ─── panels ───
BOX_TL      = "╭"
BOX_TR      = "╮"
BOX_BL      = "╰"
BOX_BR      = "╯"
BOX_H       = "─"
BOX_V       = "│"
BOX_LT      = "├"
BOX_RT      = "┤"
BOX_TT      = "┬"
BOX_BT      = "┴"
BOX_X       = "┼"

DBOX_TL     = "╔"
DBOX_TR     = "╗"
DBOX_BL     = "╚"
DBOX_BR     = "╝"
DBOX_H      = "═"
DBOX_V      = "║"

RBOX_TL     = "╭"
RBOX_TR     = "╮"
RBOX_BL     = "╰"
RBOX_BR     = "╯"

# ─── bars / charts ───
BAR_FULL    = "█"
BAR_7_8     = "▉"
BAR_3_4     = "▊"
BAR_5_8     = "▋"
BAR_1_2     = "▌"
BAR_3_8     = "▍"
BAR_1_4     = "▎"
BAR_1_8     = "▏"
BAR_EMPTY   = "░"
BAR_LIGHT   = "▒"
BAR_MED     = "▓"

SPARK_BARS  = " ▁▂▃▄▅▆▇█"
BLOCK_BARS  = " ░▒▓█"

# ─── bullets / list ───
L_DOT       = "•"
L_STAR      = "★"
L_CIRCLE    = "◉"
L_DIAMOND   = "◆"
L_ARROW     = "▸"

# ─── box drawing extended ───
H_LINE      = "─"
H_DOUBLE    = "═"
H_DOT       = "┄"
H_DASH      = "╌"
H_WAVE      = "≈"


# ─── domain icons (Nusrat's council) ───
DEPT = {
    "devops":    "⚙",
    "strategy":  "♟",
    "finance":   "৳",
    "admin":     "▤",
    "study":     "✎",
    "health":    "♥",
    "civil":     "⌂",
    "research":  "⌕",
    "relations": "☺",
    "legal":     "⚖",
    "nusrat":    "♛",
}

# ─── TUI screens ───
SCREEN = {
    "Dashboard":  "⌂",
    "Goals":      "◈",
    "Missions":   "◉",
    "Tasks":      "☑",
    "Study":      "✎",
    "Finance":    "৳",
    "Debts":      "⚖",
    "Journal":    "✐",
    "Insights":   "★",
    "Review":     "☰",
    "Predict":    "◐",
    "Plan":       "☰",
    "Voice":      "♪",
    "Vision":     "◉",
    "Profiles":   "☻",
    "Plugins":    "⚙",
    "Sync":       "↻",
    "Web":        "◐",
    "Council":    "♛",
    "Lab":        "✚",
    "Sonar":      "◉",
    "Mimi":       "✦",
    "Oath":       "✒",
    "Settings":   "⚒",
}

# ─── status indicators ───
STATUS_OK   = "✓"
STATUS_WARN = "⚠"
STATUS_FAIL = "✗"
STATUS_INFO = "ℹ"
STATUS_LOAD = "◌"
STATUS_DOT  = "●"

# ─── mood ───
MOOD = {
    "happy":    "☺",
    "sad":      "☹",
    "tired":    "◔",
    "energetic":"◕",
    "focused":  "◉",
    "calm":     "◍",
    "angry":    "◬",
}

# ─── time ───
SUN         = "☀"
MOON        = "☾"
CLOCK       = "◷"
HOURGLASS   = "⌛"

# ─── priority ───
PRIORITY = {
    "critical": "!!!",
    "high":     "!! ",
    "medium":   "!  ",
    "low":      "·  ",
}


def dept(name):
    return DEPT.get(str(name).lower(), "◇")


def screen(name):
    return SCREEN.get(name, "◇")


def mood(name):
    return MOOD.get(str(name).lower(), "◌")


def priority(p):
    return PRIORITY.get(str(p).lower(), "·  ")


# ─── emoji (for headers) ───
EMOJI = {
    "mimi":      "🤖",
    "nusrat":    "👑",
    "council":   "🏛",
    "money":     "💰",
    "fire":      "🔥",
    "spark":     "✨",
    "chart":     "📊",
    "clock":     "🕐",
    "check":     "✅",
    "cross":     "❌",
    "warn":      "⚠️",
    "rocket":    "🚀",
    "brain":     "🧠",
    "shield":    "🛡️",
    "target":    "🎯",
    "book":      "📚",
    "food":      "🍽️",
    "sleep":     "😴",
    "run":       "🏃",
    "heart":     "❤️",
    "star":      "⭐",
    "moon":      "🌙",
    "sun":       "☀️",
    "cloud":     "☁️",
    "bolt":      "⚡",
    "gem":       "💎",
    "trophy":    "🏆",
    "crown":     "👑",
    "lock":      "🔒",
    "key":       "🔑",
    "wand":      "🪄",
    "crystal":   "🔮",
    "gemstone":  "💠",
    "wave":      "🌊",
    "leaf":      "🍃",
    "eye":       "👁️",
    "ear":       "👂",
    "hand":      "✋",
    "sparkles":  "✨",
}


def emoji(name, default=None):
    return EMOJI.get(str(name).lower(), default or "◆")


# ─── logo banner ───
LOGO_BIG = r"""
   ___   ___ ___ _____ _  _   __  __ ___ __  __ ___
  / _ \ / __| _ \_   _| \| | |  \/  |_ _|  \/  |_ _|
 | (_) | (_ |   / | | | .` | | |\/| || || |\/| || |
  \___/ \___|_|_\ |_| |_|\_| |_|  |_|___|_|  |_|___|
"""

LOGO_COMPACT = "◈  M I M I  ◈"
LOGO_MARK = "◈"

# ─── sparkles gradient (for decorations) ───
SPARKLES = "✧･ﾟ: *✧･ﾟ:*  ✦  *:･ﾟ✧*:･ﾟ✧"
DIVIDER = "─" * 40
DIVIDER_THIN = "┄" * 40
DIVIDER_DOT = "· " * 20
DIVIDER_WAVE = "≈" * 40


# ─── emoji (for headers) ───
EMOJI = {
    "mimi":      "🤖",
    "nusrat":    "👑",
    "council":   "🏛",
    "money":     "💰",
    "fire":      "🔥",
    "spark":     "✨",
    "chart":     "📊",
    "clock":     "🕐",
    "check":     "✅",
    "cross":     "❌",
    "warn":      "⚠️",
    "rocket":    "🚀",
    "brain":     "🧠",
    "shield":    "🛡️",
    "target":    "🎯",
    "book":      "📚",
    "food":      "🍽️",
    "sleep":     "😴",
    "run":       "🏃",
    "heart":     "❤️",
    "star":      "⭐",
    "moon":      "🌙",
    "sun":       "☀️",
    "cloud":     "☁️",
    "bolt":      "⚡",
    "gem":       "💎",
    "trophy":    "🏆",
    "crown":     "👑",
    "lock":      "🔒",
    "key":       "🔑",
    "wand":      "🪄",
    "crystal":   "🔮",
    "gemstone":  "💠",
    "wave":      "🌊",
    "leaf":      "🍃",
    "eye":       "👁️",
    "ear":       "👂",
    "hand":      "✋",
    "sparkles":  "✨",
}


def emoji(name, default=None):
    return EMOJI.get(str(name).lower(), default or "◆")


# ─── logo banner ───
LOGO_BIG = r"""
   ___   ___ ___ _____ _  _   __  __ ___ __  __ ___
  / _ \ / __| _ \_   _| \| | |  \/  |_ _|  \/  |_ _|
 | (_) | (_ |   / | | | .` | | |\/| || || |\/| || |
  \___/ \___|_|_\ |_| |_|\_| |_|  |_|___|_|  |_|___|
"""

LOGO_COMPACT = "◈  M I M I  ◈"
LOGO_MARK = "◈"

# ─── sparkles gradient (for decorations) ───
SPARKLES = "✧･ﾟ: *✧･ﾟ:*  ✦  *:･ﾟ✧*:･ﾟ✧"
DIVIDER = "─" * 40
DIVIDER_THIN = "┄" * 40
DIVIDER_DOT = "· " * 20
DIVIDER_WAVE = "≈" * 40
