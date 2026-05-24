from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ai_game_playtesting_agent.models import Move


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    game_url: str = Field(default="https://play2048.co/", validation_alias="PLAYTEST_GAME_URL")
    artifacts_root: Path = Field(default=Path("artifacts"), validation_alias="PLAYTEST_ARTIFACTS_ROOT")
    animation_ms: int = 250
    viewport_width: int = 1280
    viewport_height: int = 800

    default_runs: int = Field(default=1, validation_alias="PLAYTEST_RUNS")
    default_max_moves: int = Field(default=50, validation_alias="PLAYTEST_MAX_MOVES")
    default_headed: bool = Field(default=False, validation_alias="PLAYTEST_HEADED")

    session_id_format: str = "%Y%m%d%H%M%S"
    screenshots_dir_name: str = "screenshots"
    logs_dir_name: str = "logs"
    moves_log_filename: str = "moves.jsonl"
    events_log_filename: str = "events.jsonl"
    report_log_filename: str = "report.jsonl"

    page_load_timeout_ms: int = 1500
    vision_temperature: float = 0.0
    report_temperature: float = 0.3
    vision_fallback_grid_size: int = 4
    vision_fallback_move: Move = "up"
