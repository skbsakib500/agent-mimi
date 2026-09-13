# Agent Mimi

**Version 6.0 "Nexus"** · Personal Life Agent for Termux

## Run

    python -m mimi            # Full-screen TUI (default)
    python -m mimi --classic  # Classic menu

## Highlights

- **40+ modules** · Goals, Missions, Tasks, Study, Finance, Health,
  Journal, Intelligence, APIs
- **Full-screen TUI** · Sidebar, live clock, framed panels
- **Command Palette** (:) · fuzzy search every action
- **Multi-profile** · separate DB per context (Personal / Work / Study)
- **Plugin system** · drop a .py into `mimi/plug_store/`
- **Cloud Sync** · Git-backed (auto pull on start, push on exit)
- **LLM Support** · Groq, Gemini, OpenAI, Anthropic, Ollama
- **Automation** · rules + scheduler + notifications
- **XP / Level / Badges** · gamified progress
- **Voice / TTS** · reads replies aloud
- **Bilingual UI** · English / বাংলা

## TUI Keys

    ↑ ↓      sidebar navigation
    Enter    open editor
    v        view latest record (modal)
    /        live search
    :        command palette
    T        cycle theme (midnight/sunset/forest)
    Y        manual sync (pull + push)
    r        refresh
    Esc      clear filter
    q        quit

## Sync

    https://github.com/skbsakib500/Mimi-data

- auto-pull at startup
- auto-push at exit
- manual: press `Y` inside TUI

## Safety

- Never delete `data/mimi.db` manually
- Destructive ops need typed confirmation
- Auto backups in `backups/`
- All destructive ops audited in `system_logs`
