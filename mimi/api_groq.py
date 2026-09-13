"""Groq LLM wrapper - OpenAI-compatible."""
from .api_manager import get as get_key
from .api_http import post_json

BASE = "https://api.groq.com/openai/v1"

MODELS = [
    "openai/gpt-oss-20b",     # fast, lightweight
    "openai/gpt-oss-120b",    # reasoning, powerful
    "moonshotai/kimi-k2-instruct",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]


def available():
    return bool(get_key("groq"))


def ask(prompt, model="openai/gpt-oss-20b", max_tokens=800, temperature=0.7):
    key = get_key("groq")
    if not key:
        return "[Groq: no API key set]"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {key}"}
    out = post_json(f"{BASE}/chat/completions", payload, headers)
    if "_error" in out:
        return f"[Groq error: {out['_error']}]"
    try:
        return out["choices"][0]["message"]["content"].strip()
    except Exception:
        return "[Groq: unexpected response]"


def main():
    from .ui import (BOLD, CYAN, DIM, GREEN, RED, WHITE,
                     c, clear, header, pause)
    clear()
    header("⚡ GROQ", "Fast Llama / Mixtral")
    if not available():
        print(c("\n  No GROQ_API_KEY set.", RED))
        print("  Free key: https://console.groq.com/keys")
        print("  Then: 7 > API Keys > 1 > groq")
        pause(); return
    print("  Model:")
    for i, m in enumerate(MODELS, 1):
        print(f"    {i}. {m}")
    sel = input("  Choose [1]: ").strip() or "1"
    try:
        model = MODELS[int(sel) - 1]
    except Exception:
        model = MODELS[0]
    print(c(f"  Using {model}", DIM + WHITE))
    print("  Type 'exit' to return.\n")
    while True:
        q = input(c("  you > ", BOLD + CYAN)).strip()
        if not q or q.lower() in ("exit", "q"):
            break
        print(c("  groq > ", BOLD + GREEN), end="")
        print(ask(q, model=model))
        print()
    pause()

run = main
