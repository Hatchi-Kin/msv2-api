from fastapi import APIRouter

from api.core.dependencies import CurrentUser, LibraryRepo, Pagination
from api.handlers.library import (
    get_album_list_from_artist_handler,
    get_artist_list_handler,
    get_random_track_handler,
    get_similar_tracks_handler,
    get_track_by_id_handler,
    get_track_count_handler,
    get_tracklist_from_album_handler,
    get_tracklist_from_artist_and_album_handler,
)
from api.models.library import AlbumList, ArtistList, SimilarTrackList, Track, TrackList

library_router = APIRouter(prefix="/library", tags=["Music library"])


@library_router.get("/track_count", response_model=int)
async def get_track_count_endpoint(
    _user: CurrentUser,
    library_repo: LibraryRepo,
):
    return await get_track_count_handler(library_repo)


@library_router.get("/random_track", response_model=Track)
async def get_random_track_endpoint(
    _user: CurrentUser,
    library_repo: LibraryRepo,
    include_embeddings: bool = False,
):
    return await get_random_track_handler(library_repo, include_embeddings)


@library_router.get("/track/{track_id}", response_model=Track)
async def get_track_by_id_endpoint(
    _user: CurrentUser,
    track_id: int,
    library_repo: LibraryRepo,
    include_embeddings: bool = False,
):
    return await get_track_by_id_handler(track_id, library_repo, include_embeddings)


@library_router.get("/artists", response_model=ArtistList)
async def get_artist_list_endpoint(
    _user: CurrentUser,
    library_repo: LibraryRepo,
    params: Pagination,
):
    return await get_artist_list_handler(library_repo, params.limit, params.offset)


@library_router.get("/albums/{artist_name}", response_model=AlbumList)
async def get_album_list_from_artist_endpoint(
    _user: CurrentUser,
    artist_name: str,
    library_repo: LibraryRepo,
):
    return await get_album_list_from_artist_handler(artist_name, library_repo)


@library_router.get("/tracks/{album_folder}", response_model=TrackList)
async def get_tracklist_from_album_endpoint(
    _user: CurrentUser,
    album_folder: str,
    library_repo: LibraryRepo,
    include_embeddings: bool = False,
):
    return await get_tracklist_from_album_handler(
        album_folder, library_repo, include_embeddings
    )


@library_router.get("/tracks/{artist_name}/{album_name}", response_model=TrackList)
async def get_tracklist_from_artist_and_album_endpoint(
    _user: CurrentUser,
    artist_name: str,
    album_name: str,
    library_repo: LibraryRepo,
    include_embeddings: bool = False,
):
    return await get_tracklist_from_artist_and_album_handler(
        artist_name, album_name, library_repo, include_embeddings
    )


@library_router.get("/similar/{track_id}", response_model=SimilarTrackList)
async def get_similar_tracks_endpoint(
    _user: CurrentUser,
    track_id: int,
    library_repo: LibraryRepo,
):
    return await get_similar_tracks_handler(track_id, library_repo)
