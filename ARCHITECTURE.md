# Architecture — Agent-Mimi

## Layer Diagram

    ┌──────────────────────────────────────────────────────┐
    │  INTERFACES (6)                                       │
    │  ──────────────────────────────────────               │
    │  TUI (curses)  Web (http.server)  CLI  iOS PWA      │
    │  ├─ tui2.py        ├─ web/server.py                  │
    │  ├─ ui.py          ├─ web/ios/shell.py (42K)         │
    │  ├─ ui2/           ├─ web/ios/pwa.py                 │
    │  └─ tui_*.py       └─ web/ios/ai_chat_api.py         │
    └──────────────────────┬───────────────────────────────┘
                           │
    ┌──────────────────────▼───────────────────────────────┐
    │  CORE LOGIC                                           │
    │  ──────────────────────────────────                   │
    │  main.py · router.py · agents/ · daemon.py            │
    │  council/ (Nusrat + 10 depts)                         │
    │  ai_plan.py · ai_chat.py · multi_ai.py · llm.py       │
    └──────────────────────┬───────────────────────────────┘
                           │
    ┌──────────────────────▼───────────────────────────────┐
    │  DOMAIN MODULES (60+)                                 │
    │  ──────────────────────────────                       │
    │  tasks · goals · study · finance · debts · daily     │
    │  sleep · journal · health · career · faith · digital │
    │  relationships · productivity · mistakes · learning  │
    │  achievements · analytics · insights · personas      │
    │  automation · recommendations · predict · trust      │
    └──────────────────────┬───────────────────────────────┘
                           │
    ┌──────────────────────▼───────────────────────────────┐
    │  DATA + TRUST                                         │
    │  ──────────────                                       │
    │  database.py → SQLite                                 │
    │  trust/      → HMAC constitution, audit chain         │
    │  guardian/   → sandbox, rollback                      │
    │  data/profiles/<name>/mimi.db (per-profile)           │
    └──────────────────────────────────────────────────────┘

## Directory Map

    Agent-Mimi/
    ├── PROJECT.md, ARCHITECTURE.md, ROADMAP.md, ...
    ├── .skb/                      project metadata
    ├── .env                       API keys (untracked)
    ├── README.md, CHANGELOG.md
    ├── backups/                   ZIP archives
    ├── data/
    │   ├── mimi.db                (untracked — runtime)
    │   ├── audit.chain            (untracked)
    │   └── profiles/<name>/mimi.db
    └── mimi/                      172 Python modules
        ├── __init__.py            __version__ = "12.0.0"
        ├── __main__.py            CLI entry
        ├── main.py                main menu / router
        ├── router.py              dispatch
        │
        ├── core/                  shared (USER_NAME, config)
        ├── agents/                department workers
        ├── council/               Nusrat + 10 brains
        ├── trust/                 HMAC, audit chain
        ├── guardian/              sandbox, rollback
        ├── health/                diagnostics
        ├── upgrade/               self-update lab
        ├── plug_store/            plugins
        ├── web/
        │   ├── server.py          HTTP routes
        │   └── ios/
        │       ├── shell.py       iOS PWA UI (42K)
        │       ├── pwa.py         PWA manifest
        │       ├── sw.py          service worker
        │       └── ai_chat_api.py chat endpoint
        │
        ├── ui2/                   TUI framework (theme, icons,
        │                          widgets, layout, anim)
        ├── tui2.py                main TUI
        ├── tui_*.py               modal, palette, themes, search
        │
        ├── ai_chat.py             multi-AI session
        ├── ai_chat_tui.py         chat TUI
        ├── multi_ai.py            7 providers
        ├── ai_plan.py             daily plan (offline + AI)
        ├── ai_context.py          context builder
        ├── ai_review.py           review engine
        ├── llm.py                 provider loader
        ├── api_*.py               Gemini/Groq/Google/HTTP/Weather
        │
        ├── daemon.py              24/7 scheduler (Termux:Boot)
        ├── telegram_bot.py        Telegram integration
        │
        └── (60+ domain modules: tasks, goals, finance, ...)

## Data Flow — AI Daily Plan

    python -m mimi → main.py
        │
        ▼
    ai_plan.plan()
        │
        ├── ai_plan.gather()
        │     ├── SQLite: tasks, study, goals, sleep, energy
        │     └── api_weather (optional)
        │
        ├── load_provider() from llm.py
        │     └── reads .env (DEEPSEEK_API_KEY, etc.)
        │
        ├── if provider: llm.chat(prompt, ...)
        │   else:        offline_plan(g)
        │
        ▼
    returns (text, context, source="AI"|"offline")
        │
        ▼
    UI renders (TUI or iOS PWA)
        │
        ▼
    optional: save to reports/plan_YYYY-MM-DD.md

## Council of 11 Brains

    Nusrat (Chairwoman)
    ├── DevOps
    ├── Strategy
    ├── Finance
    ├── Admin
    ├── Study
    ├── Health
    ├── Civil
    ├── Research
    ├── Relations
    └── Legal

Each brain = a module in `council/`.
Nusrat coordinates; decisions logged to audit chain.

## Trust Layer

    constitution.py      → HMAC-SHA256 signed rules
    trust/verify.py      → public verification
    guardian/audit.py    → append-only signed log
    guardian/            → sandbox before apply, auto-rollback

Owner-gated: only SKB Sakib can change constitution.

## Interfaces

| Command | Module | Output |
|---------|--------|--------|
| `python -m mimi` | tui2.py | curses TUI |
| `python -m mimi ios` | web/ios/shell.py | PWA at :8765/app |
| `python -m mimi app` | tui_android.py | Android-style TUI |
| `python -m mimi sonic` | sonic.py | Sonic CLI |
| `python -m mimi --classic` | ui.py | classic menu |
| `python -m mimi web` | web/server.py | dashboard |

## AI Providers

7 supported (via `multi_ai.py` + `api_*.py`):
- Gemini (`api_gemini.py`)
- Groq (`api_groq.py`)
- Google (`api_google.py`)
- OpenRouter (via api_http)
- Mistral (via api_http)
- OpenAI (via api_http)
- Anthropic (via api_http)
- DeepSeek (via api_http, `.env`)

Offline fallback: `nusrat_offline.py` (in Mimi-Android) /
rule-based planners (in Python core).

## Known Architectural Debt

    1. Version drift: __init__.py = 12.0.0, V13 features committed
    2. No requirements.txt — 172 modules, deps implicit
    3. tui2.py + tui_android.py + sonic.py — overlapping UI code
    4. web/server.py uses stdlib http.server — not async
    5. daemon.py depends on Termux:Boot (Android-only)
    6. Council/11 brains — some departments thin
    7. api_manager.py + multi_ai.py — provider registry overlap
