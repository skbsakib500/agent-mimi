"""Agent Mimi - core."""
from datetime import datetime

APP_NAME = "AGENT MIMI"
VERSION = "11.0.0"
CODENAME = "Nova"
SYSTEM = "Personal Life Agent"
USER_NAME = "SKB Sakib"
SCHEMA_VERSION = 1


def greeting():
    try:
        from .. import lang
        bn = lang._current() == "bn"
    except Exception:
        bn = False

    h = datetime.now().hour
    if bn:
        if h < 5:  return f"হ্যালো {USER_NAME} - এখনো জেগে?"
        if h < 12: return f"শুভ সকাল, {USER_NAME}"
        if h < 17: return f"শুভ অপরাহ্ন, {USER_NAME}"
        if h < 22: return f"শুভ সন্ধ্যা, {USER_NAME}"
        return f"শুভ রাত্রি, {USER_NAME} - সময় কাজে লাগান।"
    else:
        if h < 5:  return f"Hi {USER_NAME} - still up?"
        if h < 12: return f"Hi {USER_NAME} - good morning."
        if h < 17: return f"Hi {USER_NAME} - good afternoon."
        if h < 22: return f"Hi {USER_NAME} - good evening."
        return f"Hi {USER_NAME} - late night, make it count."
