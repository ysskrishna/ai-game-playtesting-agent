from ai_game_playtesting_agent.models import BoardObservation, GameEvent


def grids_equal(a: list[list[int]], b: list[list[int]]) -> bool:
    return a == b


def detect_events(
    turn: int,
    previous: BoardObservation | None,
    current: BoardObservation,
) -> list[GameEvent]:
    events: list[GameEvent] = []

    if current.game_over:
        events.append(GameEvent(turn=turn, kind="game_over", detail="Vision detected game over"))

    if current.won_2048 or current.best_tile >= 2048:
        events.append(GameEvent(turn=turn, kind="reached_2048", detail=f"best_tile={current.best_tile}"))

    if previous is None:
        return events

    if current.score > previous.score:
        events.append(GameEvent(turn=turn, kind="score_increased", detail=f"{previous.score} -> {current.score}"))

    if current.best_tile > previous.best_tile:
        events.append(GameEvent(turn=turn, kind="tile_merged", detail=f"best_tile {previous.best_tile} -> {current.best_tile}"))

    if grids_equal(previous.grid, current.grid) and current.score == previous.score and not current.game_over:
        events.append(GameEvent(turn=turn, kind="invalid_move", detail="Board unchanged after last action"))

    if previous.move == current.move and grids_equal(previous.grid, current.grid):
        events.append(GameEvent(turn=turn, kind="stall_loop", detail=f"Repeated move '{current.move}' with no change"))

    return events
