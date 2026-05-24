"""LangGraph play loop: observe → act → … → report."""

import operator
import time
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph

from playtesting_agent.browser import GameBrowser
from playtesting_agent.events import detect_events
from playtesting_agent.models import BoardObservation, GameEvent
from playtesting_agent.report import write_report
from playtesting_agent.sessions import append_jsonl
from playtesting_agent.vision import VisionObserver


class PlaytestState(TypedDict):
    session_id: str
    session_dir: str
    step: int
    actions_taken: int
    max_moves: int
    current: dict | None
    previous: dict | None
    events: Annotated[list[dict], operator.add]
    observations: Annotated[list[dict], operator.add]
    done: bool
    vision_errors: int
    started_at: float
    final_report_path: str | None


def build_graph(
    browser: GameBrowser,
    observer: VisionObserver,
    settings,
    session_dir: Path,
    session_id: str,
    max_moves: int,
):
    moves_log = session_dir / "logs" / "moves.jsonl"
    events_log = session_dir / "logs" / "events.jsonl"

    def observe(state: PlaytestState) -> dict:
        step = state["step"]
        shot_path = session_dir / "screenshots" / f"move_{step:04d}.png"
        browser.screenshot(shot_path)

        previous = BoardObservation.model_validate(state["previous"]) if state.get("previous") else None
        vision_errors = state.get("vision_errors", 0)

        try:
            current = observer.observe(shot_path)
        except Exception:
            vision_errors += 1
            current = BoardObservation(
                grid=[[0] * 4 for _ in range(4)],
                move="up",
                reasoning="vision error fallback",
                confidence="low",
            )

        append_jsonl(
            moves_log,
            {
                "turn": step,
                "move": current.move,
                "score": current.score,
                "best_tile": current.best_tile,
                "game_over": current.game_over,
                "reasoning": current.reasoning,
                "confidence": current.confidence,
                "screenshot": shot_path.name,
            },
        )

        new_events = detect_events(step, previous, current)
        for event in new_events:
            append_jsonl(events_log, event.model_dump())

        actions_taken = state.get("actions_taken", 0)
        done = current.game_over or actions_taken >= max_moves

        return {
            "step": step + 1,
            "current": current.model_dump(),
            "previous": state.get("current"),
            "events": [e.model_dump() for e in new_events],
            "observations": [current.model_dump()],
            "done": done,
            "vision_errors": vision_errors,
        }

    def act(state: PlaytestState) -> dict:
        current = BoardObservation.model_validate(state["current"])
        browser.press_move(current.move)
        return {"actions_taken": state.get("actions_taken", 0) + 1}

    def report(state: PlaytestState) -> dict:
        observations = [BoardObservation.model_validate(o) for o in state.get("observations", [])]
        events = [GameEvent.model_validate(e) for e in state.get("events", [])]
        path = write_report(
            settings,
            session_dir,
            session_id,
            observations,
            events,
            state["started_at"],
            state.get("vision_errors", 0),
        )
        return {"final_report_path": str(path)}

    def route_after_observe(state: PlaytestState) -> Literal["act", "report"]:
        return "report" if state.get("done") else "act"

    graph = StateGraph(PlaytestState)
    graph.add_node("observe", observe)
    graph.add_node("act", act)
    graph.add_node("report", report)
    graph.set_entry_point("observe")
    graph.add_conditional_edges("observe", route_after_observe, {"act": "act", "report": "report"})
    graph.add_edge("act", "observe")
    graph.add_edge("report", END)
    return graph.compile()
