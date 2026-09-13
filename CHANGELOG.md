# Changelog - Agent Mimi

## [2.0.0] - 2026-09-13 - "Zenith"

### Added
- Talk to Mimi (T): conversational agent.
  - Offline intent parser for common commands.
  - Optional LLM backend (OpenAI, Anthropic, Ollama).
- Automation Engine (monitors + rules + scheduler).
- Insights Engine (streaks, best hour, top subject, week vs week).
- Backup Center (manual DB snapshots + integrity check).
- Export (JSON + CSV).
- New modules: Faith, Learning, Career, Digital, Relationships,
  Mistakes, Achievements.

### Changed
- Single source of truth for version: mimi/core.py VERSION.
- Central DB layer with db() context manager everywhere.
- Module router handles any zero-arg main()/run().

### Fixed
- SQL placeholder mismatch in automation log write.
- Connection leaks in analytics, intelligence, data_manager.
- Missing system_logs table in foundation schema.

## [1.0.0] - 2026-09-13 - "Echo"
- Initial release: 12 modules, dashboard, analytics, data manager.
