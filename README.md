# Agent Mimi

**Version 10.0 "Guardian"** — Personal Life OS for Termux

## Council of 11 Brains

    Nusrat (Chairwoman)
    + DevOps, Strategy, Finance, Admin, Study,
      Health, Civil, Research, Relations, Legal

## Run

    python -m mimi                  # TUI
    python -m mimi --classic        # Classic menu
    python -m mimi.web.server       # Web dashboard
    python -m mimi sonic            # Sonic mode
    python -m mimi sonic council
    python -m mimi sonic nusrat status

## Safety

- Cryptographic constitution (HMAC-SHA256)
- Signed append-only audit chain
- Owner-gated permissions (SKB Sakib)
- Sandbox testing before any code change
- Automatic rollback on failure
- Auto backups in ~/.mimi/snapshots/

## Verify

    python -m mimi.trust.verify
    python -m mimi.guardian.audit verify
    python -m mimi.health.diagnostic run
