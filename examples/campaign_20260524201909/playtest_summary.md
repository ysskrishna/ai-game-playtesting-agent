# Playtesting Summary — Campaign 20260524201909

## Test Configuration

| Metric | Value |
| --- | --- |
| Game URL | https://play2048.co/ |
| Model | gpt-4o |
| Runs requested | 3 |
| Runs completed | 3 |
| Max moves per run | 20 |
| Started (UTC) | 2026-05-24T14:49:09.050247+00:00 |
| Ended (UTC) | 2026-05-24T14:51:46.219295+00:00 |

## Campaign Metrics

| Metric | Value |
| --- | --- |
| Runs completed | 3 |
| Reached 2048 (win rate) | 0 / 3 (0.0%) |
| Game over (loss rate) | 0.0% |
| Highest final score | 84 |
| Average final score | 80.0 |
| Highest best tile | 16 |
| Average best tile | 16.0 |
| Average duration (s) | 52.1 |
| Total play time (s) | 156.2 |
| Average moves per run | 20.0 |
| Actions per minute | 23.0 |
| Invalid moves (total / avg) | 2 / 0.7 |
| Stall events (total / avg) | 2 / 0.7 |
| Vision errors (total) | 0 |

## Per-Run Results

| # | Session | Score | Best tile | Moves | Duration | 2048 | Game over | Invalid | Stalls | Trace |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| 1 | `20260524201909` | 76 | 16 | 20 | 55.7s | No | No | 0 | 0 | `20260524201909/turn_log.jsonl` |
| 2 | `20260524202005` | 80 | 16 | 20 | 51.9s | No | No | 1 | 1 | `20260524202005/turn_log.jsonl` |
| 3 | `20260524202057` | 84 | 16 | 20 | 48.6s | No | No | 1 | 1 | `20260524202057/turn_log.jsonl` |

## Failure Analysis
- **Win Rate**: The campaign had 0 wins across 3 completed runs, resulting in a 0.0% win rate.
- **Score Performance**: The highest score achieved was 84, with an average score of 80.0 across sessions.
- **Tile Achievement**: The highest and average best tile reached was 16, indicating difficulty in progressing to higher tiles.
- **Invalid Moves**: A total of 2 invalid moves were recorded, averaging 0.7 per session, suggesting occasional input errors.
- **Stall Events**: 2 stall events were observed, averaging 0.7 per session, potentially indicating moments of indecision or repetitive actions.

## Behavioral Observations
- **Move Consistency**: Each session involved exactly 20 moves, showing a consistent playstyle.
- **Score Increment**: Score increased 11-13 times per session, with 2-3 tile merges, indicating moderate progress per move.
- **Action Speed**: Players maintained an average of 23 actions per minute, reflecting a steady pace.
- **Stall and Invalid Moves**: Sessions 2 and 3 each had 1 invalid move and 1 stall event, suggesting occasional strategic missteps or hesitations.
- **Game Continuity**: None of the sessions resulted in a game over, indicating that players did not reach a terminal state within the session duration.

## Suggested Improvements
- **Tutorial Enhancement**: Introduce advanced strategy tips to help players progress beyond the 16 tile and improve their win rate.
- **Feedback Mechanism**: Implement real-time feedback for invalid moves to reduce their occurrence and assist players in making valid decisions.
- **Stall Reduction**: Provide hints or suggestions during stall events to encourage more dynamic gameplay and prevent repetitive actions.
- **Pacing Adjustments**: Consider adjusting the game's pacing to encourage faster decision-making and reduce session duration, potentially increasing engagement.
- **Progress Tracking**: Introduce a progress tracker to motivate players by showing their improvement over time and setting incremental goals.
