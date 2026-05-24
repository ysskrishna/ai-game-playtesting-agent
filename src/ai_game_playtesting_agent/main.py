"""CLI: run one or more AI game playtesting sessions."""

import argparse
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

from ai_game_playtesting_agent.browser import GameBrowser
from ai_game_playtesting_agent.config import Settings
from ai_game_playtesting_agent.graph import build_graph
from ai_game_playtesting_agent.sessions import new_session_dir, write_session_meta
from ai_game_playtesting_agent.vision import VisionObserver


def run_session(settings: Settings, max_moves: int, headed: bool) -> str:
    session_id, session_dir = new_session_dir(settings)
    started_at = time.time()

    write_session_meta(
        session_dir,
        {
            "session_id": session_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "game_url": settings.game_url,
            "model": settings.openai_model,
            "max_moves": max_moves,
            "headed": headed,
        },
    )

    browser = GameBrowser(settings, headed=headed)
    observer = VisionObserver(settings)

    try:
        browser.start()
        app = build_graph(browser, observer, settings, session_dir, session_id, max_moves)
        result = app.invoke(
            {
                "session_id": session_id,
                "session_dir": str(session_dir),
                "step": 0,
                "actions_taken": 0,
                "max_moves": max_moves,
                "current": None,
                "previous": None,
                "events": [],
                "observations": [],
                "done": False,
                "vision_errors": 0,
                "started_at": started_at,
                "final_report_path": None,
            }
        )
        return result["final_report_path"]
    finally:
        browser.close()


def main() -> None:
    load_dotenv()
    settings = Settings()

    parser = argparse.ArgumentParser(description="AI game playtesting agent")
    parser.add_argument(
        "--runs", type=int, default=settings.default_runs, help="Number of gameplays (one session folder each)"
    )
    parser.add_argument(
        "--max-moves",
        type=int,
        default=settings.default_max_moves,
        help="Max arrow-key actions per gameplay",
    )
    parser.add_argument("--headed", action="store_true", default=settings.default_headed, help="Show the browser window")
    args = parser.parse_args()
    if not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY is required. Copy .env.example to .env")

    report_paths: list[str] = []
    for i in range(args.runs):
        print(f"\n--- Gameplay {i + 1}/{args.runs} ---")
        path = run_session(settings, args.max_moves, args.headed)
        print(f"Report: {path}")
        report_paths.append(path)

    print("\n=== Done ===")
    for path in report_paths:
        print(path)


if __name__ == "__main__":
    main()
