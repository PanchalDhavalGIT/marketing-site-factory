# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Marketing Site Factory — an automated pipeline that generates unique multi-page marketing websites from business listing spreadsheet data. Each site gets unique branding, design, copy, SEO, then auto-deploys to GitHub Pages with its own GitHub repo.

## Architecture

**Orchestration flow:**
```
Spreadsheet → Python Orchestrator → N concurrent Claude Code sessions
  Each session: PM Agent → sub-agents (research → brand → UX → copy → UI → frontend → SEO → CX → validate → deploy)
```

**Key layers:**
- `orchestrator/` — Python asyncio engine that reads spreadsheet, assigns themes, launches/monitors parallel Claude CLI sessions
- `dashboard/` — FastAPI + HTMX web dashboard at `localhost:3000` for controlling the entire pipeline
- `.claude/skills/` — 9 reusable skill definitions (brand-identity, ui-design, ux-flow, seo-optimizer, marketing-copy, cx-strategy, deploy-ghpages, github-publish, site-validator)
- `.claude/agents/` — 9 agent personas (project-manager orchestrates; researcher, ux-architect, copywriter, ui-designer, frontend-dev, seo-specialist, cx-analyst, deployer execute)
- `templates/` — 26 unique theme definitions with industry affinity mapping
- `validators/` — Build, SEO, and content quality checks
- `workspace/` — Isolated per-site working directories (gitignored)

## Running the Pipeline

```bash
# One-time setup
./setup.sh

# Start the dashboard (recommended)
python -m dashboard.app
# Open http://localhost:3000

# Or via CLI (dry-run first)
python -m orchestrator.main --spreadsheet data/businesses.csv --count 5 --concurrency 5 --dry-run

# Real run
python -m orchestrator.main --spreadsheet data/businesses.csv --count 5 --concurrency 5
```

## Key Constraints

- Each site MUST have a unique theme — the ThemeEngine uses locking to prevent duplicates across concurrent sessions
- All file writes within a Claude session are sandboxed to that site's `workspace/{slug}/` directory via the boundary-check hook
- PM agent is the only agent that spawns sub-agents; sub-agents do not nest further
- GitHub repos follow naming: `marketing-{business-slug}`
- Max 2 retries per site with exponential backoff on failures
- Generated sites use `output: 'export'` for static HTML (GitHub Pages compatible)
- No server components or API routes in generated sites — everything is statically exportable

## Environment

- Uses **local Claude Code CLI** (authenticated via `claude` login, no API key needed)
- `GITHUB_TOKEN` — GitHub token with `repo` and `pages` scopes

## Tech Stack Per Generated Site

- Next.js 14+ (App Router, static export)
- Tailwind CSS
- TypeScript
- Deployed on GitHub Pages via GitHub Actions

## Dashboard

The web dashboard (`dashboard/`) provides:
- **Upload** — Load spreadsheet data (CSV/Excel)
- **Monitor** — Launch batches, real-time progress tracking (HTMX auto-refresh)
- **Logs** — Per-site build log viewer
- **Sites** — Deployed sites with live GitHub Pages URLs
- **Settings** — Configure concurrency, timeouts, check credentials
- **JSON API** — `GET /api/v1/status` for external integrations
