import logging
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    db_host: str = Field(..., validation_alias="DB_HOST")
    db_port: int = Field(1433, validation_alias="DB_PORT")
    db_name: str = Field(..., validation_alias="DB_NAME")
    db_user: str = Field(..., validation_alias="DB_USER")
    db_password: str = Field(..., validation_alias="DB_PASSWORD")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:5173"],
        validation_alias="CORS_ORIGINS",
    )

    # AI
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")

    @property
    def database_url(self) -> str:
        """Build the async aioodbc connection string.

        Returns:
            SQLAlchemy-compatible async connection URL for SQL Server.
        """
        return (
            f"mssql+aioodbc://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Returns:
        Application settings singleton.
    """
    return Settings()


settings: Settings = get_settings()
