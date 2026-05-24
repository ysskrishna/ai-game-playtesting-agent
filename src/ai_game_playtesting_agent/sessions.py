import json
from datetime import datetime, timezone
from pathlib import Path


def new_session_dir(artifacts_root: Path) -> tuple[str, Path]:
    """Create artifacts/YYYYMMDDHHMMSS/ with screenshots/ and logs/."""
    artifacts_root.mkdir(parents=True, exist_ok=True)
    base_id = datetime.now().strftime("%Y%m%d%H%M%S")
    session_id = base_id
    suffix = 2
    while (artifacts_root / session_id).exists():
        session_id = f"{base_id}_{suffix}"
        suffix += 1

    session_dir = artifacts_root / session_id
    (session_dir / "screenshots").mkdir(parents=True)
    (session_dir / "logs").mkdir(parents=True)
    return session_id, session_dir


def write_session_meta(session_dir: Path, meta: dict) -> None:
    path = session_dir / "session_meta.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
