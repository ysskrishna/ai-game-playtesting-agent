import json
from datetime import datetime
from pathlib import Path

from ai_game_playtesting_agent.config import Settings


def new_session_dir(settings: Settings) -> tuple[str, Path]:
    """Create artifacts/YYYYMMDDHHMMSS/ with screenshots/ and logs/."""
    artifacts_root = settings.artifacts_root
    artifacts_root.mkdir(parents=True, exist_ok=True)
    base_id = datetime.now().strftime(settings.session_id_format)
    session_id = base_id
    suffix = 2
    while (artifacts_root / session_id).exists():
        session_id = f"{base_id}_{suffix}"
        suffix += 1

    session_dir = artifacts_root / session_id
    (session_dir / settings.screenshots_dir_name).mkdir(parents=True)
    (session_dir / settings.logs_dir_name).mkdir(parents=True)
    return session_id, session_dir


def append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
