# AI Game Playtesting Agent

Autonomous agent that plays [2048](https://play2048.co/) in a real browser, reads the board with **GPT-4o vision**, and writes a structured playtesting report per session.

## Architecture

```
CLI (main.py)
  └── for each gameplay:
        sessions.new_session_dir()  →  artifacts/YYYYMMDDHHMMSS/
        LangGraph (graph.py)
          observe → act → observe → … → report
        browser.py (Playwright)     vision.py (GPT-4o)
        events.py                   report.py
```

**LangGraph** runs a small loop: screenshot → vision → arrow key → repeat until game over or `--max-moves`. Each gameplay is an isolated **session folder** with screenshots, JSONL logs, and `playtest_report.md`.

For the design plan (architecture, LangGraph nodes, artifact layout), see [plan.md](plan.md).

## Setup

```bash
# Install dependencies
uv sync

# Install Chromium for Playwright
uv run playwright install chromium

# Configure API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

## Run

```bash
# One gameplay (default: 50 moves max)
uv run playtest

# Three gameplays, visible browser, shorter run for testing
uv run playtest --runs 3 --max-moves 30 --headed
```

## Session artifacts

Each gameplay creates:

```
artifacts/20250524143022/
  session_meta.json
  screenshots/move_0000.png ...
  logs/moves.jsonl
  logs/events.jsonl
  playtest_report.md
  playtest_report.json
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | Vision + report model |
| `PLAYTEST_GAME_URL` | `https://play2048.co/` | Game URL |
| `PLAYTEST_RUNS` | `1` | Default `--runs` when flag omitted |
| `PLAYTEST_MAX_MOVES` | `50` | Default `--max-moves` when flag omitted |
| `PLAYTEST_HEADED` | `false` | Default headed browser when flag omitted |
| `PLAYTEST_ARTIFACTS_ROOT` | `artifacts` | Root directory for session folders |

## Project layout

```
src/ai_game_playtesting_agent/
  main.py       # CLI entry
  graph.py      # LangGraph nodes and edges
  browser.py    # Playwright control
  vision.py     # GPT-4o screenshot analysis
  events.py     # Turn-to-turn event detection
  report.py     # Metrics + qualitative report
  sessions.py   # Timestamped artifact folders
  config.py     # Settings from .env
  models.py     # Pydantic schemas
```

## Reproduce a sample report

```bash
uv run playtest --runs 1 --max-moves 25 --headed
open artifacts/<session_id>/playtest_report.md
```

A committed example lives at [`reports/sample_playtest_report.md`](reports/sample_playtest_report.md).

## Cost note

Each move uses one GPT-4o vision call. A 50-move game ≈ 50 vision requests plus one text call for the report. Use `--max-moves` and `--runs` sparingly while developing.

## Limitations

- Vision-only: no DOM parsing; occasional misreads are logged.
- Depends on play2048.co layout and availability.
- Not tuned to play optimally — focused on playtesting and observation.
