from typing import Optional

from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):

    # For Kubernetes environment
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: Optional[str] = None
    MUSIC_TABLE: str = "megaset"

    # For local .env file or explicit setting
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, url_from_dotenv, info: ValidationInfo):
        if isinstance(url_from_dotenv, str) and url_from_dotenv:
            return url_from_dotenv

        user = info.data.get("POSTGRES_USER")
        password = info.data.get("POSTGRES_PASSWORD")
        host = info.data.get("POSTGRES_HOST")
        port = info.data.get("POSTGRES_PORT")
        db = info.data.get("POSTGRES_DB")

        if all([user, password, host, port, db]):
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"

        raise ValueError(
            "Database configuration is missing. Set either DATABASE_URL or all POSTGRES_* variables."
        )


class MinioSettings(BaseSettings):
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str


class AuthSettings(BaseSettings):
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"


class CORSSettings(BaseSettings):
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
        "http://msv2-webapp.192.168.1.20.nip.io",
    ]


# ----------------------------------------------- #


class Settings(DatabaseSettings, MinioSettings, AuthSettings, CORSSettings, BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)


settings = Settings()

# ----------------------------------------------- #
