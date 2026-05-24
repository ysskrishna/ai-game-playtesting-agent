from typing import Literal

from pydantic import BaseModel, Field

Move = Literal["up", "down", "left", "right", "restart"]


class BoardObservation(BaseModel):
    """GPT-4o vision output for one screenshot."""

    grid: list[list[int]] = Field(description="4x4 board; 0 means empty cell")
    score: int = 0
    best_tile: int = 0
    game_over: bool = False
    won_2048: bool = False
    move: Move
    reasoning: str = ""


class GameEvent(BaseModel):
    turn: int
    kind: str
    detail: str = ""


class SessionMetrics(BaseModel):
    moves: int
    duration_seconds: float
    final_score: int
    best_tile: int
    reached_2048: bool
    game_over: bool
    invalid_moves: int
    stall_events: int
    vision_errors: int
