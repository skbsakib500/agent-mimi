# Development Guide — Agent-Mimi

## Prerequisites

- Termux (Android) — primary target
- Python 3.14+ (`pkg install python`)
- git (`pkg install git`)
- Optional: Termux:Boot (for daemon)

## Run

    # Main TUI
    python -m mimi

    # iOS web app
    python -m mimi ios       # → http://127.0.0.1:8765/app

    # Android-style TUI
    python -m mimi app

    # Sonic CLI
    python -m mimi sonic

    # Classic menu
    python -m mimi --classic

    # Web dashboard
    python -m mimi web

## Verify Trust

    python -m mimi.trust.verify
    python -m mimi.guardian.audit verify
    python -m mimi.health.diagnostic run

## Project Layout

    mimi/
    ├── __main__.py       CLI entry
    ├── main.py           menu / router
    ├── router.py         dispatch
    ├── core/             shared config
    ├── council/          Nusrat + 10 brains
    ├── trust/            crypto constitution
    ├── guardian/         sandbox + audit
    ├── health/           diagnostics
    ├── upgrade/          self-update
    ├── web/              HTTP server + iOS PWA
    ├── ui2/              TUI framework
    └── <60+ domain modules>

## Environment (.env)

    # Add your keys — only what you use
    DEEPSEEK_API_KEY=...
    GEMINI_API_KEY=...
    GROQ_API_KEY=...
    OPENAI_API_KEY=...
    ANTHROPIC_API_KEY=...
    OPENROUTER_API_KEY=...
    MISTRAL_API_KEY=...

`.env` is gitignored. Never commit it.

## Adding a Module

1. Create `mimi/your_module.py`
2. Add DB schema (or extend `migrations.py`)
3. Add UI route (TUI: `tui2.py`, web: `router.py`)
4. Register in `router.py` if needed
5. Add to `__init__.py` if public API
6. Document in ARCHITECTURE.md

## Adding an AI Provider

Currently requires editing 2 files (known issue KI-A05):
1. `api_manager.py` — register provider
2. `multi_ai.py` — add query function

Future: single registry.

## Daemon (24/7 background)

    # Install Termux:Boot from F-Droid
    # Then:
    mkdir -p ~/.termux/boot
    cat > ~/.termux/boot/mimi-daemon.sh <<'SH'
    #!/data/data/com.termux/files/usr/bin/sh
    termux-wake-lock
    cd ~/Agent-Mimi && python -m mimi.daemon &
    SH
    chmod +x ~/.termux/boot/mimi-daemon.sh

## Commit Convention

Same as Mimi-Android:
- `feat:`  new feature
- `fix:`   bug fix
- `docs:`  documentation
- `chore:` build/deps
- `release:` version bump

## Release Checklist

- [ ] Bump `__init__.py` version
- [ ] Update CHANGELOG.md
- [ ] Update ROADMAP.md
- [ ] Update `.skb/state.json`
- [ ] Generate requirements.txt
- [ ] git commit + tag + push
- [ ] Archive ZIP to ~/Mimi-Forever/backups/

## Git Safety Rules

Never without confirmation:
- force push
- reset --hard on pushed branches
- delete remote branches
- rewrite published history

## Known Pain Points

1. No tests — manual verify only (KI-A04)
2. No requirements.txt (KI-A02)
3. TUI bugs need 3-file edits (KI-A06)
4. Daemon requires Termux:Boot (KI-A03)

## Reference

- Mobile sibling: `~/Mimi-Android`
- Backup vault: `~/Mimi-Forever`
- GitHub: https://github.com/skbsakib500/agent-mimi
