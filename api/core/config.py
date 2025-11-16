from typing import Optional

from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # For Kubernetes environment
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: Optional[str] = None

    # For local .env file or explicit setting
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, url_from_dotenv, info: ValidationInfo):
        # If DATABASE_URL is already provided (e.g., from .env), use it.
        if isinstance(url_from_dotenv, str) and url_from_dotenv:
            return url_from_dotenv

        # Otherwise, construct it from the POSTGRES_ parts for Kubernetes.
        # Access other field values through info.data
        user = info.data.get("POSTGRES_USER")
        password = info.data.get("POSTGRES_PASSWORD")
        host = info.data.get("POSTGRES_HOST")
        port = info.data.get("POSTGRES_PORT")
        db = info.data.get("POSTGRES_DB")

        if all([user, password, host, port, db]):
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"

        # If neither is provided, raise an error.
        raise ValueError(
            "Database configuration is missing. Set either DATABASE_URL or all POSTGRES_* variables."
        )

    SECRET_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
    ]


settings = Settings()
