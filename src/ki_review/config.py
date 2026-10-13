import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    github_token: str | None


def get_settings() -> Settings:
    return Settings(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        github_token=os.environ.get("GITHUB_TOKEN"),
    )
