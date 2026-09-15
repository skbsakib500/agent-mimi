# Agent-Mimi

> **SKB Dev Ecosystem · Project Identity Card**
> _Build Once. Track Everything. Update Safely. Remember Forever._

---

## Identity

| Field | Value |
|-------|-------|
| Project ID | `skb-agent-mimi` |
| Display Name | Agent Mimi |
| Version | `12.0.0` (V13 features in-flight, unreleased) |
| Type | Python application (multi-interface) |
| Status | **Active** |
| Author | SKB Dev |
| Email | msakibalmhamud5@gmail.com |
| GitHub | [skbsakib500/agent-mimi](https://github.com/skbsakib500/agent-mimi) |
| Branch | `main` |
| Python | 3.14+ |
| Files | 172 Python modules |

---

## What Is This

Agent Mimi is the **brain** of the Mimi Life OS —
a personal life-management system that runs entirely from Termux.

Six interfaces, one Python core:

    python -m mimi             # Nova TUI (curses)
    python -m mimi ios         # iOS-style web app (PWA)
    python -m mimi app         # Android-style TUI
    python -m mimi sonic       # Sonic CLI
    python -m mimi --classic   # classic menu
    python -m mimi web         # browser dashboard

- Council of 11 AI brains (Nusrat + 10 departments)
- Cryptographic constitution (HMAC-SHA256)
- Signed append-only audit chain
- Multi-provider AI (Gemini, Groq, OpenRouter, Mistral, OpenAI, Anthropic, DeepSeek)
- Offline-first, optional AI enhancement
- 24/7 daemon for background scheduling

---

## Position In Ecosystem

    Agent-Mimi (this project)  ← Python brain, source of concepts
           │  concept port
           ▼
    Mimi-Android (v1.1)        ← mobile delivery, WebView + Chaquopy
           │
           ▼
    Android users (offline)

Sibling projects:
- `Mimi-Android`   — Android delivery (active)
- `Mimi-Forever`   — backup vault
- `Mimi-APK`       — legacy builder (archived)
- `SKB-Player`     — media (separate)
- `SKB-Music`      — media (separate)
- `SKB-LifeOS`     — early attempt (archived)

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Language | Python 3.14+ |
| Storage | SQLite (on-device) |
| TUI | curses (custom framework: tui2, ui2) |
| Web | stdlib http.server (custom) |
| AI | 7 providers (see `multi_ai.py`) |
| Daemon | custom scheduler (`daemon.py`) |
| Trust | HMAC-SHA256 (`trust/`, `constitution.py`) |

---

## Memory Files

PROJECT.md · ARCHITECTURE.md · ROADMAP.md · CHANGELOG.md ·
DECISIONS.md · KNOWN-ISSUES.md · TODO.md · DEVELOPMENT.md · `.skb/`

---

_Last updated: 2026-09-15_
