import json
import time
from collections import Counter
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ai_game_playtesting_agent.config import Settings
from ai_game_playtesting_agent.models import BoardObservation, GameEvent, SessionMetrics

SYNTHESIS_PROMPT = """You are a game playtesting analyst. Write concise markdown sections based on playtest data.
Use bullet points. Be specific and grounded in the data provided. Do not invent metrics."""


def compute_metrics(
    observations: list[BoardObservation],
    events: list[GameEvent],
    duration_seconds: float,
    vision_errors: int,
) -> SessionMetrics:
    last = observations[-1] if observations else None
    invalid = sum(1 for e in events if e.kind == "invalid_move")
    stalls = sum(1 for e in events if e.kind == "stall_loop")
    return SessionMetrics(
        moves=max(0, len(observations) - 1),
        duration_seconds=round(duration_seconds, 1),
        final_score=last.score if last else 0,
        best_tile=last.best_tile if last else 0,
        reached_2048=any(e.kind == "reached_2048" for e in events),
        game_over=bool(last and last.game_over),
        invalid_moves=invalid,
        stall_events=stalls,
        vision_errors=vision_errors,
    )


def _format_table(rows: list[tuple[str, object]]) -> str:
    lines = ["| Metric | Value |", "| --- | --- |"]
    lines.extend(f"| {name} | {value} |" for name, value in rows)
    return "\n".join(lines)


def _synthesize_qualitative(settings: Settings, summary: str) -> str:
    llm = ChatOpenAI(
        model=settings.openai_model, api_key=settings.openai_api_key, temperature=settings.report_temperature
    )
    response = llm.invoke(
        [
            SystemMessage(content=SYNTHESIS_PROMPT),
            HumanMessage(
                content=(
                    "Write three markdown sections with these exact headings:\n"
                    "## Failure Analysis\n## Behavioral Observations\n## Suggested Improvements\n\n"
                    f"Playtest data:\n{summary}"
                )
            ),
        ]
    )
    return response.content if isinstance(response.content, str) else str(response.content)


def write_session_json(
    settings: Settings,
    session_dir: Path,
    session_id: str,
    session_meta: dict,
    observations: list[BoardObservation],
    events: list[GameEvent],
    started_at: float,
    vision_errors: int,
) -> Path:
    duration = time.time() - started_at
    metrics = compute_metrics(observations, events, duration, vision_errors)

    json_path = session_dir / "playtest_report.json"
    json_path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "meta": session_meta,
                "metrics": metrics.model_dump(),
                "events": [e.model_dump() for e in events],
                "observations_count": len(observations),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return json_path


def _load_session_reports(campaign_dir: Path) -> list[dict]:
    sessions: list[dict] = []
    for path in sorted(campaign_dir.glob("*/playtest_report.json")):
        sessions.append(json.loads(path.read_text(encoding="utf-8")))
    return sessions


def _sample_turns(settings: Settings, session_dir: Path, limit: int = 3) -> list[str]:
    turn_log = session_dir / settings.turn_log_filename
    if not turn_log.exists():
        return []
    samples: list[str] = []
    for line in turn_log.read_text(encoding="utf-8").splitlines()[:limit]:
        row = json.loads(line)
        samples.append(f"- turn {row.get('turn')}: {row.get('move')} — {row.get('reasoning', '')}")
    return samples


def _aggregate_metrics(sessions: list[dict]) -> dict:
    if not sessions:
        return {}

    metrics_list = [s["metrics"] for s in sessions]
    n = len(metrics_list)
    wins = sum(1 for m in metrics_list if m.get("reached_2048"))
    losses = sum(1 for m in metrics_list if m.get("game_over"))
    total_moves = sum(m.get("moves", 0) for m in metrics_list)
    total_duration = sum(m.get("duration_seconds", 0) for m in metrics_list)
    scores = [m.get("final_score", 0) for m in metrics_list]
    best_tiles = [m.get("best_tile", 0) for m in metrics_list]

    return {
        "runs_completed": n,
        "wins": wins,
        "win_rate_pct": round(100 * wins / n, 1) if n else 0,
        "loss_rate_pct": round(100 * losses / n, 1) if n else 0,
        "highest_score": max(scores),
        "average_score": round(sum(scores) / n, 1),
        "highest_best_tile": max(best_tiles),
        "average_best_tile": round(sum(best_tiles) / n, 1),
        "average_duration_seconds": round(total_duration / n, 1),
        "total_duration_seconds": round(total_duration, 1),
        "average_moves": round(total_moves / n, 1),
        "actions_per_minute": round(total_moves / total_duration * 60, 1) if total_duration > 0 else 0,
        "invalid_moves_total": sum(m.get("invalid_moves", 0) for m in metrics_list),
        "invalid_moves_avg": round(sum(m.get("invalid_moves", 0) for m in metrics_list) / n, 1),
        "stall_events_total": sum(m.get("stall_events", 0) for m in metrics_list),
        "stall_events_avg": round(sum(m.get("stall_events", 0) for m in metrics_list) / n, 1),
        "vision_errors_total": sum(m.get("vision_errors", 0) for m in metrics_list),
    }


def write_campaign_summary(
    settings: Settings,
    campaign_dir: Path,
    campaign_meta: dict,
) -> Path:
    sessions = _load_session_reports(campaign_dir)
    agg = _aggregate_metrics(sessions)
    campaign_id = campaign_meta.get("campaign_id", campaign_dir.name)

    config_rows = [
        ("Game URL", campaign_meta.get("game_url", "")),
        ("Model", campaign_meta.get("model", "")),
        ("Runs requested", campaign_meta.get("runs_requested", "")),
        ("Runs completed", agg.get("runs_completed", 0)),
        ("Max moves per run", campaign_meta.get("max_moves", "")),
        ("Started (UTC)", campaign_meta.get("started_at", "")),
        ("Ended (UTC)", campaign_meta.get("ended_at", "")),
    ]

    campaign_rows = [
        ("Runs completed", agg.get("runs_completed", 0)),
        ("Reached 2048 (win rate)", f"{agg.get('wins', 0)} / {agg.get('runs_completed', 0)} ({agg.get('win_rate_pct', 0)}%)"),
        ("Game over (loss rate)", f"{agg.get('loss_rate_pct', 0)}%"),
        ("Highest final score", agg.get("highest_score", 0)),
        ("Average final score", agg.get("average_score", 0)),
        ("Highest best tile", agg.get("highest_best_tile", 0)),
        ("Average best tile", agg.get("average_best_tile", 0)),
        ("Average duration (s)", agg.get("average_duration_seconds", 0)),
        ("Total play time (s)", agg.get("total_duration_seconds", 0)),
        ("Average moves per run", agg.get("average_moves", 0)),
        ("Actions per minute", agg.get("actions_per_minute", 0)),
        ("Invalid moves (total / avg)", f"{agg.get('invalid_moves_total', 0)} / {agg.get('invalid_moves_avg', 0)}"),
        ("Stall events (total / avg)", f"{agg.get('stall_events_total', 0)} / {agg.get('stall_events_avg', 0)}"),
        ("Vision errors (total)", agg.get("vision_errors_total", 0)),
    ]

    per_run_header = (
        "| # | Session | Score | Best tile | Moves | Duration | 2048 | Game over | Invalid | Stalls | Trace |\n"
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |"
    )
    per_run_lines = [per_run_header]
    for i, session in enumerate(sessions, start=1):
        sid = session["session_id"]
        m = session["metrics"]
        per_run_lines.append(
            f"| {i} | `{sid}` | {m.get('final_score', 0)} | {m.get('best_tile', 0)} | "
            f"{m.get('moves', 0)} | {m.get('duration_seconds', 0)}s | "
            f"{'Yes' if m.get('reached_2048') else 'No'} | {'Yes' if m.get('game_over') else 'No'} | "
            f"{m.get('invalid_moves', 0)} | {m.get('stall_events', 0)} | `{sid}/{settings.turn_log_filename}` |"
        )

    llm_parts = [f"campaign_id={campaign_id}", f"campaign_metrics={agg}"]
    for session in sessions:
        sid = session["session_id"]
        events = session.get("events", [])
        kinds = Counter(e.get("kind", "") for e in events)
        session_dir = campaign_dir / sid
        llm_parts.append(f"\nsession={sid}\nmetrics={session['metrics']}\nevent_counts={dict(kinds)}")
        samples = _sample_turns(settings, session_dir)
        if samples:
            llm_parts.append("sample_turns:\n" + "\n".join(samples))

    try:
        qualitative = _synthesize_qualitative(settings, "\n".join(llm_parts))
    except Exception as exc:
        qualitative = (
            f"## Failure Analysis\n\n(Synthesis skipped: {exc})\n\n"
            f"## Behavioral Observations\n\nSee session `turn_log.jsonl` files.\n\n"
            "## Suggested Improvements\n\nN/A"
        )

    body = f"""# Playtesting Summary — Campaign {campaign_id}

## Test Configuration

{_format_table(config_rows)}

## Campaign Metrics

{_format_table(campaign_rows)}

## Per-Run Results

{chr(10).join(per_run_lines)}

{qualitative}
"""

    md_path = campaign_dir / "playtest_summary.md"
    md_path.write_text(body, encoding="utf-8")
    return md_path
