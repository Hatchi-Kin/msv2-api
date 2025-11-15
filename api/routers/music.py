from fastapi import APIRouter
from api.core.dependencies import MusicRepo, CurrentUser
from api.models.music import MegasetTrack, ArtistList, AlbumList, TrackList
from api.handlers.music import (
    get_random_song_handler,
    get_song_count_handler,
    get_song_by_id_handler,
    get_artist_list_handler,
    get_album_list_from_artist_handler,
    get_tracklist_from_album_handler,
    get_tracklist_from_artist_and_album_handler,
)

router = APIRouter(prefix="/music", tags=["Music Metadata"])


@router.get("/song_count", response_model=int)
async def get_song_count_endpoint(music_repo: MusicRepo, _user: CurrentUser):
    """Get total song count."""
    return await get_song_count_handler(music_repo)


@router.get("/random_song", response_model=MegasetTrack)
async def get_random_song_endpoint(
    include_embeddings: bool = False,
    music_repo: MusicRepo = None,
    _user: CurrentUser = None,
):
    """Get a random song."""
    return await get_random_song_handler(include_embeddings, music_repo)


@router.get("/song/{song_id}", response_model=MegasetTrack)
async def get_song_by_id_endpoint(
    song_id: int,
    include_embeddings: bool = False,
    music_repo: MusicRepo = None,
    _user: CurrentUser = None,
):
    """Get song by ID."""
    return await get_song_by_id_handler(song_id, include_embeddings, music_repo)


@router.get("/artists", response_model=ArtistList)
async def get_artist_list_endpoint(music_repo: MusicRepo, _user: CurrentUser):
    """Get all artists."""
    return await get_artist_list_handler(music_repo)


@router.get("/albums/{artist_name}", response_model=AlbumList)
async def get_album_list_from_artist_endpoint(
    artist_name: str,
    music_repo: MusicRepo,
    _user: CurrentUser,
):
    """Get albums for artist."""
    return await get_album_list_from_artist_handler(artist_name, music_repo)


@router.get("/tracks/{album_folder}", response_model=TrackList)
async def get_tracklist_from_album_endpoint(
    album_folder: str,
    include_embeddings: bool = False,
    music_repo: MusicRepo = None,
    _user: CurrentUser = None,
):
    """Get tracks from album."""
    return await get_tracklist_from_album_handler(album_folder, include_embeddings, music_repo)


@router.get("/tracks/{artist_name}/{album_name}", response_model=TrackList)
async def get_tracklist_from_artist_and_album_endpoint(
    artist_name: str,
    album_name: str,
    include_embeddings: bool = False,
    music_repo: MusicRepo = None,
    _user: CurrentUser = None,
):
    """Get tracks from artist and album."""
    return await get_tracklist_from_artist_and_album_handler(
        artist_name, album_name, include_embeddings, music_repo
    )
