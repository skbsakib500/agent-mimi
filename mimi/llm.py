"""Agent Mimi - pluggable LLM layer.

Default: offline (no LLM). Enable a provider via env vars:

    export MIMI_LLM_PROVIDER=openai
    export OPENAI_API_KEY=sk-...

    export MIMI_LLM_PROVIDER=anthropic
    export ANTHROPIC_API_KEY=sk-ant-...

    export MIMI_LLM_PROVIDER=ollama
    # talks to http://localhost:11434 by default
"""
import os, json, urllib.request, urllib.error


class LLM:
    def __init__(self, provider, api_key=None, model=None, base_url=None):
        self.provider = provider
        self.api_key = api_key
        self.model = model or self._default_model()
        self.base_url = base_url or self._default_base()

    def _default_model(self):
        return {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-latest",
            "ollama": "llama3.2",
        }.get(self.provider, "")

    def _default_base(self):
        return {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "ollama": "http://localhost:11434",
        }.get(self.provider, "")

    def chat(self, system, messages, max_tokens=500, temperature=0.7):
        try:
            if self.provider == "openai":
                return self._openai(system, messages, max_tokens, temperature)
            if self.provider == "anthropic":
                return self._anthropic(system, messages, max_tokens, temperature)
            if self.provider == "ollama":
                return self._ollama(system, messages, temperature)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            return f"[LLM HTTP {e.code}: {body}]"
        except Exception as e:
            return f"[LLM error: {type(e).__name__}: {e}]"
        return "[unknown provider]"

    def _post(self, url, headers, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _openai(self, system, messages, max_tokens, temperature):
        msgs = [{"role": "system", "content": system}] + messages
        payload = {"model": self.model, "messages": msgs,
                   "max_tokens": max_tokens, "temperature": temperature}
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        out = self._post(f"{self.base_url}/chat/completions", headers, payload)
        return out["choices"][0]["message"]["content"].strip()

    def _anthropic(self, system, messages, max_tokens, temperature):
        payload = {"model": self.model, "system": system, "messages": messages,
                   "max_tokens": max_tokens, "temperature": temperature}
        headers = {"x-api-key": self.api_key,
                   "anthropic-version": "2023-06-01",
                   "Content-Type": "application/json"}
        out = self._post(f"{self.base_url}/messages", headers, payload)
        return out["content"][0]["text"].strip()

    def _ollama(self, system, messages, temperature):
        msgs = [{"role": "system", "content": system}] + messages
        payload = {"model": self.model, "messages": msgs,
                   "stream": False, "options": {"temperature": temperature}}
        headers = {"Content-Type": "application/json"}
        out = self._post(f"{self.base_url}/api/chat", headers, payload)
        return out["message"]["content"].strip()


def load_provider():
    provider = os.environ.get("MIMI_LLM_PROVIDER", "").strip().lower()
    if not provider:
        return None
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key: return None
        return LLM("openai", api_key=key)
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key: return None
        return LLM("anthropic", api_key=key)
    if provider == "ollama":
        return LLM("ollama")
    return None
