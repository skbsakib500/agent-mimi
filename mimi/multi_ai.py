"""Multi-AI Router - one interface, many LLMs.

Providers:
  - deepseek  (deepseek-chat, deepseek-reasoner)
  - groq      (llama 3.3, mixtral)
  - gemini    (gemini-3.6-flash)
  - openai    (gpt-4o-mini)
  - anthropic (claude-haiku)
  - ollama    (local)

Usage:
  from mimi.multi_ai import ask, ask_many
  ask("hello", provider="deepseek")
  ask_many("hello")   # returns dict: {provider: reply}
"""
from .api_manager import get as get_key

PROVIDERS = {
    "deepseek":  {
        "name": "DeepSeek",
        "env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "available_fn": lambda: bool(get_key("deepseek")),
    },
    "groq":      {
        "name": "Groq",
        "env": "GROQ_API_KEY",
        "default_model": "openai/gpt-oss-20b",
        "available_fn": lambda: bool(get_key("groq")),
    },
    "gemini":    {
        "name": "Gemini",
        "env": "GEMINI_API_KEY",
        "default_model": "gemini-3.6-flash",
        "available_fn": lambda: bool(get_key("gemini")),
    },
    "openai":    {
        "name": "OpenAI",
        "env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
        "available_fn": lambda: bool(get_key("openai")),
    },
    "anthropic": {
        "name": "Anthropic",
        "env": "ANTHROPIC_API_KEY",
        "default_model": "claude-3-5-haiku-latest",
        "available_fn": lambda: bool(get_key("anthropic")),
    },
    "ollama":    {
        "name": "Ollama (local)",
        "env": "",
        "default_model": "llama3.2",
        "available_fn": lambda: True,  # local; may or may not be running
    },
}


def available_providers():
    """Return list of providers with keys set."""
    return [k for k, v in PROVIDERS.items() if v["available_fn"]()]


def status():
    return {k: v["available_fn"]() for k, v in PROVIDERS.items()}


def ask(prompt, provider="deepseek", model=None, system=None,
        max_tokens=800, temperature=0.7, history=None):
    """Route a single query to one provider. Returns text reply."""
    if provider not in PROVIDERS:
        return f"[unknown provider: {provider}]"
    if not PROVIDERS[provider]["available_fn"]():
        return f"[{provider} not configured]"

    model = model or PROVIDERS[provider]["default_model"]
    try:
        if provider == "deepseek":
            return _deepseek(prompt, model, system, max_tokens, temperature, history)
        if provider == "groq":
            return _groq(prompt, model, system, max_tokens, temperature, history)
        if provider == "gemini":
            return _gemini(prompt, model, system, max_tokens, temperature, history)
        if provider == "openai":
            return _openai(prompt, model, system, max_tokens, temperature, history)
        if provider == "anthropic":
            return _anthropic(prompt, model, system, max_tokens, temperature, history)
        if provider == "ollama":
            return _ollama(prompt, model, system, temperature, history)
    except Exception as e:
        return f"[{provider} error: {type(e).__name__}: {e}]"
    return f"[unhandled provider: {provider}]"


def ask_many(prompt, providers=None, **kwargs):
    """Ask multiple providers in parallel (threaded). Returns dict."""
    import concurrent.futures as cf
    providers = providers or available_providers()
    if not providers:
        return {}
    out = {}
    with cf.ThreadPoolExecutor(max_workers=min(6, len(providers))) as ex:
        futs = {ex.submit(ask, prompt, provider=p, **kwargs): p for p in providers}
        for f in cf.as_completed(futs):
            p = futs[f]
            try:
                out[p] = f.result(timeout=60)
            except Exception as e:
                out[p] = f"[error: {e}]"
    return out


# ─── Provider implementations ───

def _deepseek(prompt, model, system, max_tokens, temp, history):
    from .api_http import post_json
    key = get_key("deepseek")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    if history:
        msgs.extend(history[-10:])
    msgs.append({"role": "user", "content": prompt})
    out = post_json("https://api.deepseek.com/v1/chat/completions", {
        "model": model, "messages": msgs,
        "max_tokens": max_tokens, "temperature": temp,
    }, headers={"Authorization": f"Bearer {key}"})
    if "_error" in out:
        return f"[deepseek: {out['_error']}]"
    return out["choices"][0]["message"]["content"].strip()


def _groq(prompt, model, system, max_tokens, temp, history):
    from .api_http import post_json
    key = get_key("groq")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    out = post_json("https://api.groq.com/openai/v1/chat/completions", {
        "model": model, "messages": msgs,
        "max_tokens": max_tokens, "temperature": temp,
    }, headers={"Authorization": f"Bearer {key}"})
    if "_error" in out:
        return f"[groq: {out['_error']}]"
    return out["choices"][0]["message"]["content"].strip()


def _gemini(prompt, model, system, max_tokens, temp, history):
    from .api_http import post_json
    key = get_key("gemini")
    parts = []
    if system:
        parts.append({"text": system + "\n\n" + prompt})
    else:
        parts.append({"text": prompt})
    out = post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        {"contents": [{"parts": parts}],
         "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temp}})
    if "_error" in out:
        return f"[gemini: {out['_error']}]"
    try:
        return out["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return "[gemini: unexpected response]"


def _openai(prompt, model, system, max_tokens, temp, history):
    from .api_http import post_json
    key = get_key("openai")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    out = post_json("https://api.openai.com/v1/chat/completions", {
        "model": model, "messages": msgs,
        "max_tokens": max_tokens, "temperature": temp,
    }, headers={"Authorization": f"Bearer {key}"})
    if "_error" in out:
        return f"[openai: {out['_error']}]"
    return out["choices"][0]["message"]["content"].strip()


def _anthropic(prompt, model, system, max_tokens, temp, history):
    from .api_http import post_json
    key = get_key("anthropic")
    out = post_json("https://api.anthropic.com/v1/messages", {
        "model": model,
        "system": system or "",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": temp,
    }, headers={"x-api-key": key,
                "anthropic-version": "2023-06-01"})
    if "_error" in out:
        return f"[anthropic: {out['_error']}]"
    try:
        return out["content"][0]["text"].strip()
    except Exception:
        return "[anthropic: unexpected response]"


def _ollama(prompt, model, system, temp, history):
    from .api_http import post_json
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    out = post_json("http://localhost:11434/api/chat", {
        "model": model, "messages": msgs, "stream": False,
        "options": {"temperature": temp},
    })
    if "_error" in out:
        return f"[ollama: {out['_error']}]"
    return out.get("message", {}).get("content", "[no reply]").strip()
