"""LangGraph play loop: observe → act → … → report."""

import operator
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph

from ai_game_playtesting_agent.browser import GameBrowser
from ai_game_playtesting_agent.config import Settings
from ai_game_playtesting_agent.events import detect_events, update_blocked_moves
from ai_game_playtesting_agent.models import BoardObservation, GameEvent, Move
from ai_game_playtesting_agent.report import write_report
from ai_game_playtesting_agent.sessions import append_jsonl
from ai_game_playtesting_agent.vision import VisionObserver


class PlaytestState(TypedDict):
    session_id: str
    session_dir: str
    step: int
    actions_taken: int
    max_moves: int
    current: dict | None
    events: Annotated[list[dict], operator.add]
    observations: Annotated[list[dict], operator.add]
    done: bool
    vision_errors: int
    blocked_moves: list[str]
    started_at: float
    final_report_path: str | None


def build_graph(
    browser: GameBrowser,
    observer: VisionObserver,
    settings: Settings,
    session_dir: Path,
    session_id: str,
    session_meta: dict,
    max_moves: int,
):
    moves_log = session_dir / settings.logs_dir_name / settings.moves_log_filename

    def observe(state: PlaytestState) -> dict:
        step = state["step"]
        shot_path = session_dir / settings.screenshots_dir_name / f"move_{step:04d}.png"
        browser.screenshot(shot_path)

        # Board before the action we just applied: last observe's `current`, not `previous`.
        before_action = BoardObservation.model_validate(state["current"]) if state.get("current") else None
        vision_errors = state.get("vision_errors", 0)
        blocked_hint: list[Move] = list(state.get("blocked_moves") or [])

        try:
            current = observer.observe(shot_path, blocked_moves=blocked_hint or None)
        except Exception:
            vision_errors += 1
            size = settings.vision_fallback_grid_size
            current = BoardObservation(
                grid=[[0] * size for _ in range(size)],
                move=settings.vision_fallback_move,
                reasoning="vision error fallback",
            )

        new_events = detect_events(step, before_action, current)
        blocked_moves = update_blocked_moves(blocked_hint, before_action, current, new_events)

        log_entry: dict = {
            "turn": step,
            "move": current.move,
            "score": current.score,
            "best_tile": current.best_tile,
            "game_over": current.game_over,
            "reasoning": current.reasoning,
            "screenshot": shot_path.name,
        }
        if blocked_hint:
            log_entry["blocked_moves_hint"] = blocked_hint
        append_jsonl(moves_log, log_entry)

        actions_taken = state.get("actions_taken", 0)
        done = current.game_over or actions_taken >= max_moves

        return {
            "step": step + 1,
            "current": current.model_dump(),
            "events": [e.model_dump() for e in new_events],
            "observations": [current.model_dump()],
            "done": done,
            "vision_errors": vision_errors,
            "blocked_moves": blocked_moves,
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
            session_meta,
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
