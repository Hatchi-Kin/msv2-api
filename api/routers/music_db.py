from fastapi import APIRouter

from api.core.dependencies import MusicRepo, CurrentUser
from api.models.music_db import MegasetTrack, ArtistList, AlbumList, TrackList, SimilarTrackList
from api.handlers.music_db import (
    get_random_track_handler,
    get_track_count_handler,
    get_track_by_id_handler,
    get_artist_list_handler,
    get_album_list_from_artist_handler,
    get_tracklist_from_album_handler,
    get_tracklist_from_artist_and_album_handler,
    get_similar_tracks_handler,
)

music_db_router = APIRouter(prefix="/music", tags=["Music Metadata"])


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


@music_db_router.get("/similar/{track_id}", response_model=SimilarTrackList)
async def get_similar_tracks_endpoint(
    _user: CurrentUser,
    track_id: int,
    music_repo: MusicRepo,
):
    return await get_similar_tracks_handler(track_id, music_repo)
