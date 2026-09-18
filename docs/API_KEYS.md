# API Keys & Services

Every service this project uses. **Never put key values in this file.** Keys live only in `.env` (and, once deployed, in Replit Secrets).

Rotate every 3 months. The Claude scheduled task `rotate-shelf-librarian-keys` (17th of Mar/Jun/Sep/Dec) covers the shared Anthropic key; this file is the record for this project.

## Services

| Service | Used for | Key name | `.env` variable | Expires | Restrictions | Spending limit | Last rotated |
|---|---|---|---|---|---|---|---|
| Anthropic (console.anthropic.com) | Cartographer, the council, LLM judge in evals | `shelf-librarian` (shared with the Sultan) | `ANTHROPIC_API_KEY` | 90 days | none available | set under Settings → Limits | 2026-09-17 |

Notes:
- The same Anthropic key serves both projects for now. If Majlis gets deployed with live runs (PRD §21), create a separate `majlis-prod` key so one project's leak doesn't affect the other, and add a row here.
- No ElevenLabs key is used here; the copy of `.env` in this repo holds the Anthropic key only.
- v1 is precomputed, so no key ships to production.
