from typing import Annotated

import asyncpg
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from minio import Minio

from api.core.security import validate_token_and_get_user
from api.models.auth import UserInDB
from api.models.requests import (
    NeighborsParams,
    PaginationParams,
    PointsPaginationParams,
    SearchParams,
)
from api.repositories.auth import AuthRepository
from api.repositories.coordinates import CoordinatesRepository
from api.repositories.favorites import FavoritesRepository
from api.repositories.metadata import MetadataRepository
from api.repositories.objects import ObjectsRepository
from api.repositories.playlists import PlaylistsRepository


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


def get_metadata_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> MetadataRepository:
    """Get MetadataRepository instance."""
    return MetadataRepository(pool)


def get_favorites_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> FavoritesRepository:
    """Get FavoritesRepository instance."""
    return FavoritesRepository(pool)


def get_playlists_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> PlaylistsRepository:
    """Get PlaylistsRepository instance."""
    return PlaylistsRepository(pool)


def get_coordinates_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> CoordinatesRepository:
    """Get CoordinatesRepository instance."""
    return CoordinatesRepository(pool)


def get_objects_repository(minio_client: Minio = Depends(get_minio_client)) -> ObjectsRepository:
    """Get ObjectsRepository instance."""
    return ObjectsRepository(minio_client)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_repo: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> UserInDB:
    """Get the current authenticated user from JWT token."""
    return await validate_token_and_get_user(token, auth_repo)


# Type aliases for cleaner injection

# Repositories
AuthRepo = Annotated[AuthRepository, Depends(get_auth_repository)]
MetadataRepo = Annotated[MetadataRepository, Depends(get_metadata_repository)]
FavoritesRepo = Annotated[FavoritesRepository, Depends(get_favorites_repository)]
PlaylistsRepo = Annotated[PlaylistsRepository, Depends(get_playlists_repository)]
CoordinatesRepo = Annotated[CoordinatesRepository, Depends(get_coordinates_repository)]
ObjectsRepo = Annotated[ObjectsRepository, Depends(get_objects_repository)]

# Clients
MinioClient = Annotated[Minio, Depends(get_minio_client)]

# Auth
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]

# Query Parameters
Pagination = Annotated[PaginationParams, Depends()]
PointsPagination = Annotated[PointsPaginationParams, Depends()]
Search = Annotated[SearchParams, Depends()]
Neighbors = Annotated[NeighborsParams, Depends()]
