from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # PostgreSQL connection settings loaded from the root .env file.
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Local Ollama configuration. These can also be overridden in .env.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5vl:3b"

    # Local models can take longer, especially when running on the CPU.
    ollama_timeout_seconds: float = 300.0

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


settings = Settings()  # type: ignore[call-arg]