from fastapi import APIRouter

from api.core.dependencies import CurrentUser, FavoritesRepo
from api.handlers.favorites import (
    add_favorite_handler,
    check_favorite_handler,
    get_favorites_handler,
    remove_favorite_handler,
)
from api.models.favorites import FavoriteCheckResponse
from api.models.library import FavoritesList
from api.models.responses import OperationResult

favorites_router = APIRouter(prefix="/user", tags=["User's Favorites"])


@favorites_router.post("/favorites/{track_id}", response_model=OperationResult)
async def add_favorite_endpoint(
    track_id: int,
    current_user: CurrentUser,
    favorites_repo: FavoritesRepo,
):
    return await add_favorite_handler(current_user.id, track_id, favorites_repo)


@favorites_router.delete("/favorites/{track_id}", response_model=OperationResult)
async def remove_favorite_endpoint(
    track_id: int,
    current_user: CurrentUser,
    favorites_repo: FavoritesRepo,
):
    return await remove_favorite_handler(current_user.id, track_id, favorites_repo)


@favorites_router.get("/favorites", response_model=FavoritesList)
async def get_favorites_endpoint(
    current_user: CurrentUser,
    favorites_repo: FavoritesRepo,
):
    return await get_favorites_handler(current_user.id, favorites_repo)


@favorites_router.get(
    "/favorites/check/{track_id}", response_model=FavoriteCheckResponse
)
async def check_favorite_endpoint(
    track_id: int,
    current_user: CurrentUser,
    favorites_repo: FavoritesRepo,
):
    return await check_favorite_handler(current_user.id, track_id, favorites_repo)
