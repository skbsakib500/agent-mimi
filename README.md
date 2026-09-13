# Agent Mimi

**Version 7.0 "Aurora Web"** — Personal Life Agent for Termux

## Three ways to run

    python -m mimi                # Full-screen TUI (curses)
    python -m mimi --classic      # Classic menu
    python -m mimi.web.server     # Web dashboard (browser)

Web dashboard URL: http://127.0.0.1:8765/

## Highlights

- **40+ modules** — Goals, Missions, Tasks, Study, Finance, Health, Journal
- **TUI** — sidebar, command palette, themes, mouse, live clock
- **Web dashboard** — PWA installable, live charts, add/complete/delete tasks
- **Agent** — Talk to Mimi (offline + LLM: Groq, Gemini, OpenAI, Anthropic, Ollama)
- **Multi-profile** — separate DB per context
- **Plugin system** — drop .py into `mimi/plug_store/`
- **Cloud sync** — Git-backed, auto pull/push
- **XP / Levels / Badges** — gamified progress
- **Voice** — Termux TTS reads replies
- **Notifications** — Termux:API push
- **Bilingual** — English / বাংলা

## TUI Keys

    ↑ ↓      sidebar navigation
    Enter    open editor
    v        view latest record (modal)
    /        live search
    :        command palette
    T        cycle theme
    Y        manual sync
    r        refresh
    q        quit (+ auto-push)

## Safety

- Never delete `data/mimi.db` manually
- Destructive ops need typed confirmation
- Auto backups in `backups/`
- All destructive ops logged in `system_logs`
