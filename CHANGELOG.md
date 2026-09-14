# Changelog — Agent Mimi

## [10.0.0] — "Guardian"

### Added
- Council of 11 Brains (Nusrat + 10 departments)
- Cryptographic constitution (HMAC-SHA256, key at ~/.mimi/keys)
- Append-only signed audit chain
- Owner-gated permissions with refuse-list
- Upgrade Lab (detect → propose → sandbox → apply → rollback)
- Department Factory (Mimi can propose new departments)
- Health Diagnostic (Sonar)
- Sonic CLI

### Security
- Constitution signature verified at every boot
- Key chmod 600 enforced
- Refuse-list cannot be bypassed
- Sandbox isolated from production data/

## [9.0.0] — "Echo"    Web chat, voice, vision
## [7.0.0] — "Aurora"  Web dashboard + PWA
## [6.0.0] — "Nexus"   Multi-profile, plugins, cloud sync
## [5.0.0] — "Quantum" TUI
## [4.0.0] — "Oracle"  Briefing, LLM APIs
## [3.0.0] — "Nova"    XP, levels, badges
## [2.0.0] — "Zenith"  Agent, insights, automation
