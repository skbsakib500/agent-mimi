"""Bilingual strings (EN / BN) + toggle."""
import os
from .database import fetch_one, execute

BN = {
    "greeting_morning":   "শুভ সকাল",
    "greeting_afternoon": "শুভ অপরাহ্ন",
    "greeting_evening":   "শুভ সন্ধ্যা",
    "greeting_night":     "শুভ রাত্রি",
    "welcome":            "স্বাগতম",
    "dashboard":          "ড্যাশবোর্ড",
    "categories":         "বিভাগসমূহ",
    "command":            "আদেশ",
    "growth":             "বৃদ্ধি",
    "finance":            "অর্থ",
    "life":               "জীবন",
    "mind":               "মন",
    "intelligence":       "বুদ্ধিমত্তা",
    "quick_actions":      "দ্রুত কাজ",
    "exit":               "প্রস্থান",
    "back":               "ফিরে যান",
    "add":                "যোগ করুন",
    "list":               "তালিকা",
    "update":             "হালনাগাদ",
    "summary":            "সারসংক্ষেপ",
    "exit_menu":          "বের হন",
    "invalid":            "ভুল অপশন",
    "saved":              "সংরক্ষিত হয়েছে",
    "motto":              "নীতিবাক্য",
    "level":              "স্তর",
    "badges":             "ব্যাজ",
    "progress":           "অগ্রগতি",
    "report":             "প্রতিবেদন",
    "export":             "রপ্তানি",
    "backup":             "ব্যাকআপ",
    "notifications":      "বিজ্ঞপ্তি",
    "pomodoro":           "পোমোডোরো",
    "talk_to_mimi":       "মিমির সাথে কথা",
    "select":             "নির্বাচন",
    "today":              "আজ",
    "week":               "সপ্তাহ",
    "study":              "পড়াশোনা",
    "tasks":              "কাজ",
    "goals":              "লক্ষ্য",
    "missions":           "মিশন",
}


def _current():
    try:
        r = fetch_one("SELECT value FROM system_config WHERE key='lang'")
        return (r["value"] if r and r["value"] else "en").lower()
    except Exception:
        return "en"


def set_lang(code):
    code = code.lower()
    if code not in ("en", "bn"):
        return False
    execute("""INSERT INTO system_config (key, value, description)
               VALUES ('lang', ?, 'UI language')
               ON CONFLICT(key) DO UPDATE SET
               value=excluded.value,
               updated_at=CURRENT_TIMESTAMP""", (code,))
    return True


def get(key, default=None):
    if _current() == "bn":
        return BN.get(key, default if default is not None else key)
    return default if default is not None else key


def toggle():
    cur = _current()
    new = "bn" if cur == "en" else "en"
    set_lang(new)
    return new
