from fastapi import APIRouter

from api.core.dependencies import CurrentUser, MetadataRepo, Pagination
from api.handlers.metadata import (
    get_album_list_from_artist_handler,
    get_artist_list_handler,
    get_random_track_handler,
    get_similar_tracks_handler,
    get_track_by_id_handler,
    get_track_count_handler,
    get_tracklist_from_album_handler,
    get_tracklist_from_artist_and_album_handler,
)
from api.models.metadata import AlbumList, ArtistList, SimilarTrackList, Track, TrackList

metadata_router = APIRouter(prefix="/music", tags=["Music Metadata"])


# Metadata endpoints
@metadata_router.get("/track_count", response_model=int)
async def get_track_count_endpoint(
    _user: CurrentUser,
    metadata_repo: MetadataRepo,
):
    return await get_track_count_handler(metadata_repo)


@metadata_router.get("/random_track", response_model=Track)
async def get_random_track_endpoint(
    _user: CurrentUser,
    metadata_repo: MetadataRepo,
    include_embeddings: bool = False,
):
    return await get_random_track_handler(metadata_repo, include_embeddings)


@metadata_router.get("/track/{track_id}", response_model=Track)
async def get_track_by_id_endpoint(
    _user: CurrentUser,
    track_id: int,
    metadata_repo: MetadataRepo,
    include_embeddings: bool = False,
):
    return await get_track_by_id_handler(track_id, metadata_repo, include_embeddings)


@metadata_router.get("/artists", response_model=ArtistList)
async def get_artist_list_endpoint(
    _user: CurrentUser,
    metadata_repo: MetadataRepo,
    params: Pagination,
):
    return await get_artist_list_handler(metadata_repo, params.limit, params.offset)


@metadata_router.get("/albums/{artist_name}", response_model=AlbumList)
async def get_album_list_from_artist_endpoint(
    _user: CurrentUser,
    artist_name: str,
    metadata_repo: MetadataRepo,
):
    return await get_album_list_from_artist_handler(artist_name, metadata_repo)


@metadata_router.get("/tracks/{album_folder}", response_model=TrackList)
async def get_tracklist_from_album_endpoint(
    _user: CurrentUser,
    album_folder: str,
    metadata_repo: MetadataRepo,
    include_embeddings: bool = False,
):
    return await get_tracklist_from_album_handler(album_folder, metadata_repo, include_embeddings)


@metadata_router.get("/tracks/{artist_name}/{album_name}", response_model=TrackList)
async def get_tracklist_from_artist_and_album_endpoint(
    _user: CurrentUser,
    artist_name: str,
    album_name: str,
    metadata_repo: MetadataRepo,
    include_embeddings: bool = False,
):
    return await get_tracklist_from_artist_and_album_handler(
        artist_name, album_name, metadata_repo, include_embeddings
    )


@metadata_router.get("/similar/{track_id}", response_model=SimilarTrackList)
async def get_similar_tracks_endpoint(
    _user: CurrentUser,
    track_id: int,
    metadata_repo: MetadataRepo,
):
    return await get_similar_tracks_handler(track_id, metadata_repo)
