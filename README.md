# AI Game Playtesting Agent

Autonomous agent that plays [2048](https://play2048.co/) in a real browser, reads the board with **GPT-4o vision**, and writes a structured playtesting summary per campaign.

## Architecture

```
CLI (main.py)
  └── new_campaign_dir()  →  artifacts/campaign_<id>/
        for each gameplay:
          new_session_dir()  →  campaign_<id>/<session_id>/
          LangGraph (graph.py): observe → act → … → write_session_json
        write_campaign_summary()  →  playtest_summary.md
```

**LangGraph** runs a small loop: screenshot → vision → arrow key → repeat until game over or `--max-moves`. Each CLI invocation creates one **campaign** with nested session folders and a single summary report.

For the design plan, see [plan.md](plan.md).

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

## Artifacts

Each CLI run creates:

```
artifacts/campaign_20250524143000/
  playtest_summary.md
  20250524143005/
    playtest_report.json
    turn_log.jsonl
    screenshots/move_0000.png ...
  20250524143112/
    ...
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
| `PLAYTEST_ARTIFACTS_ROOT` | `artifacts` | Root directory for campaign folders |

## Project layout

```
src/ai_game_playtesting_agent/
  main.py       # CLI entry
  graph.py      # LangGraph nodes and edges
  browser.py    # Playwright control
  vision.py     # GPT-4o screenshot analysis
  events.py     # Turn-to-turn event detection
  report.py     # Session JSON + campaign summary
  sessions.py   # Campaign and session folders
  config.py     # Settings from .env
  models.py     # Pydantic schemas
```

## Reproduce a sample report

```bash
uv run playtest --runs 1 --max-moves 25 --headed
open artifacts/campaign_*/playtest_summary.md
```

A committed example lives at [`reports/sample_playtest_summary.md`](reports/sample_playtest_summary.md).

## Cost note

Each move uses one GPT-4o vision call. A 50-move game ≈ 50 vision requests plus one text call for the campaign summary. Use `--max-moves` and `--runs` sparingly while developing.

## Limitations

- Vision-only: no DOM parsing; occasional misreads are logged.
- Depends on play2048.co layout and availability.
- Not tuned to play optimally — focused on playtesting and observation.
