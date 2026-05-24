import json
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ai_game_playtesting_agent.config import Settings
from ai_game_playtesting_agent.models import BoardObservation, GameEvent, SessionMetrics
from ai_game_playtesting_agent.sessions import append_jsonl

SYNTHESIS_PROMPT = """You are a game playtesting analyst. Write concise markdown sections based on session logs.
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


def _format_metrics_table(metrics: SessionMetrics) -> str:
    rows = [
        ("Moves (actions)", metrics.moves),
        ("Duration (seconds)", metrics.duration_seconds),
        ("Final score", metrics.final_score),
        ("Best tile", metrics.best_tile),
        ("Reached 2048", metrics.reached_2048),
        ("Game over", metrics.game_over),
        ("Invalid moves", metrics.invalid_moves),
        ("Stall events", metrics.stall_events),
        ("Vision errors", metrics.vision_errors),
    ]
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
                    f"Session data:\n{summary}"
                )
            ),
        ]
    )
    return response.content if isinstance(response.content, str) else str(response.content)


def write_report(
    settings: Settings,
    session_dir: Path,
    session_id: str,
    observations: list[BoardObservation],
    events: list[GameEvent],
    started_at: float,
    vision_errors: int,
) -> Path:
    duration = time.time() - started_at
    metrics = compute_metrics(observations, events, duration, vision_errors)

    moves_log = session_dir / settings.logs_dir_name / settings.moves_log_filename
    sample_reasoning = []
    if moves_log.exists():
        for line in moves_log.read_text(encoding="utf-8").splitlines()[:5]:
            row = json.loads(line)
            sample_reasoning.append(f"- turn {row.get('turn')}: {row.get('move')} — {row.get('reasoning', '')}")

    summary = (
        f"session_id={session_id}\n"
        f"metrics={metrics.model_dump()}\n"
        f"events={[e.model_dump() for e in events]}\n"
        f"sample_moves:\n" + "\n".join(sample_reasoning)
    )

    try:
        qualitative = _synthesize_qualitative(settings, summary)
    except Exception as exc:
        qualitative = (
            f"## Failure Analysis\n\n(Synthesis skipped: {exc})\n\n"
            f"## Behavioral Observations\n\nSee logs in `{settings.logs_dir_name}/`.\n\n"
            "## Suggested Improvements\n\nN/A"
        )

    screenshot_refs = sorted((session_dir / settings.screenshots_dir_name).glob("*.png"))
    shots_md = "\n".join(f"- `{p.relative_to(session_dir)}`" for p in screenshot_refs[:10])
    if len(screenshot_refs) > 10:
        shots_md += f"\n- ... and {len(screenshot_refs) - 10} more"

    body = f"""# Playtesting Report — Session {session_id}

## Gameplay Metrics

{_format_metrics_table(metrics)}

## Screenshots

{shots_md or "_No screenshots captured._"}

## Event Log Summary

"""
    for event in events[-20:]:
        body += f"- **{event.kind}** (turn {event.turn}): {event.detail}\n"

    logs = settings.logs_dir_name
    body += (
        f"\n{qualitative}\n\n---\n\n"
        f"Full logs: `{logs}/{settings.moves_log_filename}`, `{logs}/{settings.events_log_filename}`\n"
    )

    md_path = session_dir / "playtest_report.md"
    md_path.write_text(body, encoding="utf-8")

    json_path = session_dir / "playtest_report.json"
    json_path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "metrics": metrics.model_dump(),
                "events": [e.model_dump() for e in events],
                "observations_count": len(observations),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    append_jsonl(
        session_dir / settings.logs_dir_name / settings.report_log_filename,
        {"session_id": session_id, "report": str(md_path.name), "metrics": metrics.model_dump()},
    )

    return md_path
