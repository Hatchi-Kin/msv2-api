from fastapi import APIRouter

from api.core.dependencies import CurrentUser, PlaylistsRepo
from api.handlers.playlists import (
    add_track_to_playlist_handler,
    create_playlist_handler,
    delete_playlist_handler,
    get_playlist_detail_handler,
    get_playlists_handler,
    remove_track_from_playlist_handler,
    update_playlist_handler,
)
from api.models.metadata import (
    CreatePlaylistRequest,
    PlaylistDetail,
    PlaylistsList,
    PlaylistSummary,
    UpdatePlaylistRequest,
)
from api.models.responses import OperationResult

playlists_router = APIRouter(prefix="/music", tags=["User's Playlists"])


@playlists_router.post("/playlists", response_model=PlaylistSummary)
async def create_playlist_endpoint(
    request: CreatePlaylistRequest,
    current_user: CurrentUser,
    playlists_repo: PlaylistsRepo,
):
    return await create_playlist_handler(current_user.id, request.name, playlists_repo)


@playlists_router.get("/playlists", response_model=PlaylistsList)
async def get_playlists_endpoint(
    current_user: CurrentUser,
    playlists_repo: PlaylistsRepo,
):
    return await get_playlists_handler(current_user.id, playlists_repo)


@playlists_router.get("/playlists/{playlist_id}", response_model=PlaylistDetail)
async def get_playlist_detail_endpoint(
    playlist_id: int,
    current_user: CurrentUser,
    playlists_repo: PlaylistsRepo,
):
    return await get_playlist_detail_handler(current_user.id, playlist_id, playlists_repo)


@playlists_router.put("/playlists/{playlist_id}", response_model=OperationResult)
async def update_playlist_endpoint(
    playlist_id: int,
    request: UpdatePlaylistRequest,
    current_user: CurrentUser,
    playlists_repo: PlaylistsRepo,
):
    return await update_playlist_handler(current_user.id, playlist_id, request.name, playlists_repo)


@playlists_router.delete("/playlists/{playlist_id}", response_model=OperationResult)
async def delete_playlist_endpoint(
    playlist_id: int,
    current_user: CurrentUser,
    playlists_repo: PlaylistsRepo,
):
    return await delete_playlist_handler(current_user.id, playlist_id, playlists_repo)


@playlists_router.post("/playlists/{playlist_id}/tracks/{track_id}", response_model=OperationResult)
async def add_track_to_playlist_endpoint(
    playlist_id: int,
    track_id: int,
    current_user: CurrentUser,
    playlists_repo: PlaylistsRepo,
):
    return await add_track_to_playlist_handler(
        current_user.id, playlist_id, track_id, playlists_repo
    )


@playlists_router.delete(
    "/playlists/{playlist_id}/tracks/{track_id}", response_model=OperationResult
)
async def remove_track_from_playlist_endpoint(
    playlist_id: int,
    track_id: int,
    current_user: CurrentUser,
    playlists_repo: PlaylistsRepo,
):
    return await remove_track_from_playlist_handler(
        current_user.id, playlist_id, track_id, playlists_repo
    )
