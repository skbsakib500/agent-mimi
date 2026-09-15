"""Multi-AI chat engine.

Session state, history, provider selection, parallel queries.
"""
from datetime import datetime
from .multi_ai import ask, ask_many, available_providers, PROVIDERS


class ChatSession:
    def __init__(self, system=None, history_size=10):
        self.system = system or (
            "You are a helpful, concise assistant. "
            "Answer in the user's language. Keep replies under 200 words."
        )
        self.history_size = history_size
        self.history = []       # [{"role":"user"|"assistant","content":..., "provider":...}]
        self.created = datetime.now().isoformat(timespec="seconds")

    def _build_history(self):
        return [{"role": h["role"], "content": h["content"]}
                for h in self.history[-self.history_size:]]

    def ask_one(self, prompt, provider="deepseek", **kwargs):
        hist = self._build_history()
        self.history.append({"role": "user", "content": prompt})
        reply = ask(prompt, provider=provider,
                    system=self.system, history=hist, **kwargs)
        self.history.append({"role": "assistant", "content": reply,
                             "provider": provider})
        return reply

    def ask_all(self, prompt, providers=None, **kwargs):
        hist = self._build_history()
        self.history.append({"role": "user", "content": prompt})
        replies = ask_many(prompt, providers=providers,
                           system=self.system, history=hist, **kwargs)
        for provider, reply in replies.items():
            self.history.append({"role": "assistant",
                                  "content": reply, "provider": provider})
        return replies

    def clear(self):
        self.history = []

    def stats(self):
        return {
            "turns": len(self.history) // 2,
            "total_msgs": len(self.history),
            "created": self.created,
            "system": self.system[:60] + ("..." if len(self.system) > 60 else ""),
        }
