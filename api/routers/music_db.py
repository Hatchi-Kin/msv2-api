from fastapi import APIRouter

from api.core.dependencies import MusicRepo, CurrentUser
from api.models.music_db import (
    MegasetTrack,
    ArtistList,
    AlbumList,
    TrackList,
    SimilarTrackList,
    FavoritesList,
    PlaylistsList,
    PlaylistDetail,
    PlaylistSummary,
    CreatePlaylistRequest,
    UpdatePlaylistRequest,
)
from api.handlers.music_db import (
    get_random_track_handler,
    get_track_count_handler,
    get_track_by_id_handler,
    get_artist_list_handler,
    get_album_list_from_artist_handler,
    get_tracklist_from_album_handler,
    get_tracklist_from_artist_and_album_handler,
    get_similar_tracks_handler,
    add_favorite_handler,
    remove_favorite_handler,
    get_favorites_handler,
    check_favorite_handler,
    create_playlist_handler,
    get_playlists_handler,
    get_playlist_detail_handler,
    update_playlist_handler,
    delete_playlist_handler,
    add_track_to_playlist_handler,
    remove_track_from_playlist_handler,
)


music_db_router = APIRouter(prefix="/music", tags=["Music Metadata"])

# ----------------------------------------------- #


@music_db_router.get("/track_count", response_model=int)
async def get_track_count_endpoint(
    _user: CurrentUser,
    music_repo: MusicRepo,
):
    return await get_track_count_handler(music_repo)


@music_db_router.get("/random_track", response_model=MegasetTrack)
async def get_random_track_endpoint(
    _user: CurrentUser,
    music_repo: MusicRepo,
    include_embeddings: bool = False,
):
    return await get_random_track_handler(music_repo, include_embeddings)


@music_db_router.get("/track/{track_id}", response_model=MegasetTrack)
async def get_track_by_id_endpoint(
    _user: CurrentUser,
    track_id: int,
    music_repo: MusicRepo,
    include_embeddings: bool = False,
):
    return await get_track_by_id_handler(track_id, music_repo, include_embeddings)


@music_db_router.get("/artists", response_model=ArtistList)
async def get_artist_list_endpoint(
    _user: CurrentUser,
    music_repo: MusicRepo,
    limit: int = 100,
    offset: int = 0,
):
    return await get_artist_list_handler(music_repo, limit, offset)


@music_db_router.get("/albums/{artist_name}", response_model=AlbumList)
async def get_album_list_from_artist_endpoint(
    _user: CurrentUser,
    artist_name: str,
    music_repo: MusicRepo,
):
    return await get_album_list_from_artist_handler(artist_name, music_repo)


@music_db_router.get("/tracks/{album_folder}", response_model=TrackList)
async def get_tracklist_from_album_endpoint(
    _user: CurrentUser,
    album_folder: str,
    music_repo: MusicRepo,
    include_embeddings: bool = False,
):
    return await get_tracklist_from_album_handler(album_folder, music_repo, include_embeddings)


@music_db_router.get("/tracks/{artist_name}/{album_name}", response_model=TrackList)
async def get_tracklist_from_artist_and_album_endpoint(
    _user: CurrentUser,
    artist_name: str,
    album_name: str,
    music_repo: MusicRepo,
    include_embeddings: bool = False,
):
    return await get_tracklist_from_artist_and_album_handler(
        artist_name, album_name, music_repo, include_embeddings
    )


# ----------------------------------------------- #


@music_db_router.post("/favorites/{track_id}")
async def add_favorite_endpoint(
    track_id: int,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await add_favorite_handler(current_user.id, track_id, music_repo)


@music_db_router.delete("/favorites/{track_id}")
async def remove_favorite_endpoint(
    track_id: int,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await remove_favorite_handler(current_user.id, track_id, music_repo)


@music_db_router.get("/favorites", response_model=FavoritesList)
async def get_favorites_endpoint(
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await get_favorites_handler(current_user.id, music_repo)


@music_db_router.get("/favorites/check/{track_id}")
async def check_favorite_endpoint(
    track_id: int,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await check_favorite_handler(current_user.id, track_id, music_repo)


# ----------------------------------------------- #


@music_db_router.post("/playlists", response_model=PlaylistSummary)
async def create_playlist_endpoint(
    request: CreatePlaylistRequest,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await create_playlist_handler(current_user.id, request.name, music_repo)


@music_db_router.get("/playlists", response_model=PlaylistsList)
async def get_playlists_endpoint(
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await get_playlists_handler(current_user.id, music_repo)


@music_db_router.get("/playlists/{playlist_id}", response_model=PlaylistDetail)
async def get_playlist_detail_endpoint(
    playlist_id: int,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await get_playlist_detail_handler(current_user.id, playlist_id, music_repo)


@music_db_router.put("/playlists/{playlist_id}")
async def update_playlist_endpoint(
    playlist_id: int,
    request: UpdatePlaylistRequest,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await update_playlist_handler(current_user.id, playlist_id, request.name, music_repo)


@music_db_router.delete("/playlists/{playlist_id}")
async def delete_playlist_endpoint(
    playlist_id: int,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await delete_playlist_handler(current_user.id, playlist_id, music_repo)


@music_db_router.post("/playlists/{playlist_id}/tracks/{track_id}")
async def add_track_to_playlist_endpoint(
    playlist_id: int,
    track_id: int,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await add_track_to_playlist_handler(current_user.id, playlist_id, track_id, music_repo)


@music_db_router.delete("/playlists/{playlist_id}/tracks/{track_id}")
async def remove_track_from_playlist_endpoint(
    playlist_id: int,
    track_id: int,
    current_user: CurrentUser,
    music_repo: MusicRepo,
):
    return await remove_track_from_playlist_handler(current_user.id, playlist_id, track_id, music_repo)


# ----------------------------------------------- #


@music_db_router.get("/similar/{track_id}", response_model=SimilarTrackList)
async def get_similar_tracks_endpoint(
    _user: CurrentUser,
    track_id: int,
    music_repo: MusicRepo,
):
    return await get_similar_tracks_handler(track_id, music_repo)
