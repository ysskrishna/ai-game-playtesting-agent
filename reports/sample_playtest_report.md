# Playtesting Report — Session 20250524120000

> Example structure. Run `uv run playtest` to generate a real report under `artifacts/<YYYYMMDDHHMMSS>/`.

## Gameplay Metrics

| Metric | Value |
| --- | --- |
| Moves (actions) | 42 |
| Duration (seconds) | 186.3 |
| Final score | 2844 |
| Best tile | 256 |
| Reached 2048 | false |
| Game over | true |
| Invalid moves | 2 |
| Stall events | 1 |
| Vision errors | 0 |

## Screenshots

- `screenshots/move_0000.png`
- `screenshots/move_0010.png`
- `screenshots/game_over.png`

## Event Log Summary

- **score_increased** (turn 3): 24 -> 56
- **tile_merged** (turn 8): best_tile 32 -> 64
- **invalid_move** (turn 15): Board unchanged after last action
- **game_over** (turn 42): Vision detected game over

## Failure Analysis

- Agent boxed high tiles in the center instead of keeping a corner strategy.
- Two invalid moves suggest the model misread near-identical board states.

## Behavioral Observations

- Preferred horizontal merges early; shifted to vertical moves under pressure.
- Did not recover after a stall loop at turn 28–31.

## Suggested Improvements

- Tutorial hint about corner strategy could reduce early random swiping.
- Game-over overlay is clear; retry flow worked without agent confusion.

---

Full logs: `logs/moves.jsonl`, `logs/events.jsonl`
