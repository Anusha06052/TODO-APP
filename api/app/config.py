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
    db_name: str = Field(..., validation_alias="DB_NAME")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:5173"],
        validation_alias="CORS_ORIGINS",
    )

   
    @property
    def database_url(self) -> str:
        """Build the async aioodbc connection string.

        Returns:
            SQLAlchemy-compatible async connection URL for SQL Server.
        """
        return (
            f"mssql+aioodbc://@{self.db_host}/{self.db_name}"
            f"?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Returns:
        Application settings singleton.
    """
    return Settings()


settings: Settings = get_settings()
