from typing import Annotated

from fastapi import Request, Depends
from fastapi.security import OAuth2PasswordBearer
import asyncpg
from minio import Minio

from api.core.security import validate_token_and_get_user
from api.models.auth import UserInDB
from api.repositories.auth import AuthRepository
from api.repositories.music_db import MusicRepository
from api.repositories.music_storage import StorageRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get asyncpg pool from application state."""
    return request.app.state.db_pool


def get_minio_client(request: Request) -> Minio:
    """Get MinIO client from application state."""
    return request.app.state.minio_client


def get_auth_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> AuthRepository:
    """Get AuthRepository instance."""
    return AuthRepository(pool)


def get_music_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> MusicRepository:
    """Get MusicRepository instance."""
    return MusicRepository(pool)


def get_storage_repository(minio_client: Minio = Depends(get_minio_client)) -> StorageRepository:
    """Get StorageRepository instance."""
    return StorageRepository(minio_client)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_repo: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> UserInDB:
    """Get the current authenticated user from JWT token."""
    return await validate_token_and_get_user(token, auth_repo)


# Type aliases for cleaner injection
AuthRepo = Annotated[AuthRepository, Depends(get_auth_repository)]
MusicRepo = Annotated[MusicRepository, Depends(get_music_repository)]
StorageRepo = Annotated[StorageRepository, Depends(get_storage_repository)]
MinioClient = Annotated[Minio, Depends(get_minio_client)]
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]
