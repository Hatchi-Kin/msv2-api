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
from api.repositories.inference import InferenceRepository
from api.repositories.library import LibraryRepository
from api.repositories.media import MediaRepository
from api.repositories.playlists import PlaylistsRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get asyncpg pool from application state."""
    return request.app.state.db_pool


def get_minio_client(request: Request) -> Minio:
    return request.app.state.minio_client


def get_auth_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> AuthRepository:
    return AuthRepository(pool)


def get_library_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> LibraryRepository:
    return LibraryRepository(pool)


def get_favorites_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> FavoritesRepository:
    return FavoritesRepository(pool)


def get_playlists_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> PlaylistsRepository:
    return PlaylistsRepository(pool)


def get_coordinates_repository(pool: asyncpg.Pool = Depends(get_db_pool)) -> CoordinatesRepository:
    return CoordinatesRepository(pool)


def get_media_repository(minio_client: Minio = Depends(get_minio_client)) -> MediaRepository:
    return MediaRepository(minio_client)


def get_inference_repository() -> InferenceRepository:
    """Get InferenceRepository instance."""
    return InferenceRepository()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_repo: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> UserInDB:
    """Get the current authenticated user from JWT token."""
    return await validate_token_and_get_user(token, auth_repo)


## Type aliases for cleaner injection

# Repositories
AuthRepo = Annotated[AuthRepository, Depends(get_auth_repository)]
LibraryRepo = Annotated[LibraryRepository, Depends(get_library_repository)]
FavoritesRepo = Annotated[FavoritesRepository, Depends(get_favorites_repository)]
PlaylistsRepo = Annotated[PlaylistsRepository, Depends(get_playlists_repository)]
CoordinatesRepo = Annotated[CoordinatesRepository, Depends(get_coordinates_repository)]
MediaRepo = Annotated[MediaRepository, Depends(get_media_repository)]
InferenceRepo = Annotated[InferenceRepository, Depends(get_inference_repository)]

# Clients
MinioClient = Annotated[Minio, Depends(get_minio_client)]

# Auth
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]

# Query Parameters
Pagination = Annotated[PaginationParams, Depends()]
PointsPagination = Annotated[PointsPaginationParams, Depends()]
Search = Annotated[SearchParams, Depends()]
Neighbors = Annotated[NeighborsParams, Depends()]
