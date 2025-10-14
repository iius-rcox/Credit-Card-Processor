"""
Configuration management using pydantic-settings.

This module loads and validates environment variables for the application.
"""

from typing import Literal, Optional

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        ENVIRONMENT: Deployment environment (development/production/test)
        LOG_LEVEL: Logging level (DEBUG/INFO/WARNING/ERROR)

        DATABASE_URL: PostgreSQL connection string (async format)
        POSTGRES_HOST: PostgreSQL hostname
        POSTGRES_PORT: PostgreSQL port
        POSTGRES_DB: Database name
        POSTGRES_USER: Database user
        POSTGRES_PASSWORD: Database password

        REDIS_URL: Redis connection string (optional)
        REDIS_HOST: Redis hostname (optional)
        REDIS_PORT: Redis port (optional)

        AZURE_KEY_VAULT_NAME: Azure Key Vault name (for production)
        AZURE_TENANT_ID: Azure AD tenant ID (for production)
        AZURE_CLIENT_ID: Azure AD client ID (for production)

        MAX_UPLOAD_SIZE_MB: Maximum file upload size in MB
        MAX_UPLOAD_COUNT: Maximum number of files per upload
        TEMP_STORAGE_PATH: Path for temporary file storage
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Environment
    ENVIRONMENT: Literal["development", "production", "test"] = Field(
        default="development",
        description="Deployment environment"
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )

    # Database (PostgreSQL)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://ccprocessor:password@localhost:5432/credit_card_db",
        description="PostgreSQL async connection string"
    )
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL hostname")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="credit_card_db", description="Database name")
    POSTGRES_USER: str = Field(default="ccprocessor", description="Database user")
    POSTGRES_PASSWORD: str = Field(default="password", description="Database password")

    # Redis (optional, for caching and background jobs)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection string"
    )
    REDIS_HOST: Optional[str] = Field(default="localhost", description="Redis hostname")
    REDIS_PORT: Optional[int] = Field(default=6379, description="Redis port")

    # Azure (for production secrets management)
    AZURE_KEY_VAULT_NAME: Optional[str] = Field(
        default=None,
        description="Azure Key Vault name"
    )
    AZURE_TENANT_ID: Optional[str] = Field(
        default=None,
        description="Azure AD tenant ID"
    )
    AZURE_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="Azure AD client ID"
    )

    # Upload settings
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=10,
        description="Maximum file upload size in MB"
    )
    MAX_UPLOAD_COUNT: int = Field(
        default=100,
        description="Maximum number of files per upload"
    )

    # CORS settings
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "https://credit-card.ii-us.com"],
        description="Allowed CORS origins"
    )

    # API settings
    API_V1_PREFIX: str = Field(
        default="/api",
        description="API version 1 prefix"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL uses async driver."""
        if v and not v.startswith("postgresql+asyncpg://"):
            # Convert sync URL to async
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    def get_max_upload_size_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Create global settings instance
settings = Settings()


# Helper functions for common checks
def is_production() -> bool:
    """Check if running in production environment."""
    return settings.ENVIRONMENT == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.ENVIRONMENT == "development"


def is_test() -> bool:
    """Check if running in test environment."""
    return settings.ENVIRONMENT == "test"
