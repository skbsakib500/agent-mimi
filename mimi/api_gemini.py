"""Google Gemini API wrapper."""
from .api_manager import get as get_key
from .api_http import post_json, get_json

BASE = "https://generativelanguage.googleapis.com/v1beta"


def available():
    return bool(get_key("gemini"))


def ask(prompt, model="gemini-3.6-flash", max_tokens=800, temperature=0.7):
    key = get_key("gemini")
    if not key:
        return "[Gemini: no API key. Add via API Keys menu.]"
    url = f"{BASE}/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        },
    }
    out = post_json(url, payload)
    if "_error" in out:
        return f"[Gemini error: {out['_error']}]"
    try:
        return out["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return "[Gemini: unexpected response shape]"


def models():
    key = get_key("gemini")
    if not key:
        return []
    out = get_json(f"{BASE}/models?key={key}")
    if "_error" in out:
        return []
    return [m["name"].split("/")[-1]
            for m in out.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE,
                     c, clear, header, pause, section)
    if not available():
        clear()
        header("✨ GEMINI", "API key required")
        print(c("\n  No GEMINI_API_KEY set.", RED))
        print("  Get a free key: https://aistudio.google.com/apikey")
        print("  Then: 6 > API Keys > 1")
        pause()
        return
    clear()
    header("✨ GEMINI", "Chat with Google AI")
    print("  Type 'exit' to return.\n")
    while True:
        q = input(c("  you > ", BOLD + CYAN)).strip()
        if not q or q.lower() in ("exit", "quit", "q"):
            break
        print(c("  gemini > ", BOLD + GREEN), end="")
        print(ask(q))
        print()
    pause()

run = main
