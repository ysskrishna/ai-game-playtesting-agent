from ai_game_playtesting_agent.models import BoardObservation, GameEvent, Move


def grids_equal(a: list[list[int]], b: list[list[int]]) -> bool:
    return a == b


def board_changed(previous: BoardObservation, current: BoardObservation) -> bool:
    return current.score > previous.score or not grids_equal(previous.grid, current.grid)


def update_blocked_moves(
    blocked_moves: list[Move],
    previous: BoardObservation | None,
    current: BoardObservation,
    new_events: list[GameEvent],
) -> list[Move]:
    """Track directions that had no effect; cleared after a successful action."""
    if previous is None:
        return []

    if board_changed(previous, current):
        return []

    failed_kinds = {"invalid_move", "stall_loop"}
    if not any(e.kind in failed_kinds for e in new_events):
        return list(blocked_moves)

    failed_move = previous.move
    if failed_move == "restart":
        return list(blocked_moves)

    updated = list(blocked_moves)
    if failed_move not in updated:
        updated.append(failed_move)
    return updated


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
