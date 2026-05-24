from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    game_url: str = Field(default="https://play2048.co/", validation_alias="PLAYTEST_GAME_URL")
    artifacts_root: Path = Path("artifacts")
    animation_ms: int = 250
    viewport_width: int = 1280
    viewport_height: int = 800
