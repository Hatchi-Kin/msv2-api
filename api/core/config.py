from typing import Optional

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):

    # PostgreSQL settings
    AUTH_TABLE: str = "users"
    MUSIC_TABLE: str = "megaset"
    FAVORITES_TABLE: str = "favorites"
    PLAYLISTS_TABLE: str = "playlists"
    PLAYLIST_TRACKS_TABLE: str = "playlist_tracks"
    TRACK_VIZ_TABLE: str = "track_visualization"
    EMBEDDINGS_COLUMN: str = "embedding_512_vector"

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


class BusinessRulesSettings(BaseSettings):
    """Business logic configuration."""

    MAX_FAVORITES_PER_USER: int = 20
    MAX_PLAYLIST_TRACKS: int = 20

    # Similarity search: Query more candidates (30) to allow filtering by artist diversity,
    # then return top 9 tracks with max 1 per artist for varied recommendations
    SIMILAR_TRACKS_LIMIT: int = 30
    SIMILAR_TRACKS_RETURNED: int = 9

    # API query limits (max values users can request)
    MAX_ARTIST_LIMIT: int = 500
    MAX_POINTS_LIMIT: int = 5000
    MAX_SEARCH_LIMIT: int = 200
    MAX_NEIGHBORS_LIMIT: int = 100

    # Default values when not specified
    DEFAULT_ARTIST_LIMIT: int = 100
    DEFAULT_POINTS_LIMIT: int = 1000
    DEFAULT_SEARCH_LIMIT: int = 50
    DEFAULT_NEIGHBORS_LIMIT: int = 20

    AUDIO_STREAM_CHUNK_SIZE: int = 32 * 1024  # 32KB


class CORSSettings(BaseSettings):
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
        "http://msv2-webapp.192.168.1.20.nip.io",
        "https://webapp.msv2.ovh",
        "https://www.webapp.msv2.ovh"
    ]


# ----------------------------------------------- #


class Settings(
    DatabaseSettings, MinioSettings, AuthSettings, CORSSettings, BusinessRulesSettings, BaseSettings
):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)


settings = Settings()

# ----------------------------------------------- #
