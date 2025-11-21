from api.core.config import settings
from api.core.exceptions import MaxLimitException, NotFoundException
from api.models.library import PlaylistDetail, PlaylistsList, PlaylistSummary
from api.models.responses import OperationResult
from api.repositories.playlists import PlaylistsRepository


async def create_playlist_handler(
    user_id: int, name: str, playlists_repo: PlaylistsRepository
) -> PlaylistSummary:
    result = await playlists_repo.create_playlist(user_id, name)
    return PlaylistSummary(**result)


async def get_playlists_handler(user_id: int, playlists_repo: PlaylistsRepository) -> PlaylistsList:
    playlists = await playlists_repo.get_user_playlists(user_id)
    return PlaylistsList(playlists=[PlaylistSummary(**p) for p in playlists])


async def get_playlist_detail_handler(
    user_id: int, playlist_id: int, playlists_repo: PlaylistsRepository
) -> PlaylistDetail:
    result = await playlists_repo.get_playlist_detail(user_id, playlist_id)
    if not result:
        raise NotFoundException("Playlist", str(playlist_id))
    return PlaylistDetail(**result)


async def update_playlist_handler(
    user_id: int, playlist_id: int, new_name: str, playlists_repo: PlaylistsRepository
) -> OperationResult:
    updated = await playlists_repo.update_playlist_name(user_id, playlist_id, new_name)
    if not updated:
        raise NotFoundException("Playlist", str(playlist_id))
    return OperationResult(success=True, message="Playlist name updated")


async def delete_playlist_handler(
    user_id: int, playlist_id: int, playlists_repo: PlaylistsRepository
) -> OperationResult:
    deleted = await playlists_repo.delete_playlist(user_id, playlist_id)
    if not deleted:
        raise NotFoundException("Playlist", str(playlist_id))
    return OperationResult(success=True, message="Playlist deleted")


async def add_track_to_playlist_handler(
    user_id: int, playlist_id: int, track_id: int, playlists_repo: PlaylistsRepository
) -> OperationResult:
    # Check if playlist exists and belongs to user
    if not await playlists_repo.playlist_exists(user_id, playlist_id):
        raise NotFoundException("Playlist", str(playlist_id))

    # Check track count
    count = await playlists_repo.get_playlist_track_count(playlist_id)
    if count >= settings.MAX_PLAYLIST_TRACKS:
        raise MaxLimitException("playlist tracks", settings.MAX_PLAYLIST_TRACKS)

    # Check if track exists
    if not await playlists_repo.track_exists(track_id):
        raise NotFoundException("Track", str(track_id))

    # Add track
    added = await playlists_repo.add_track_to_playlist(user_id, playlist_id, track_id)
    message = "Track added to playlist" if added else "Track already in playlist"
    return OperationResult(success=added, message=message)


async def remove_track_from_playlist_handler(
    user_id: int, playlist_id: int, track_id: int, playlists_repo: PlaylistsRepository
) -> OperationResult:
    # Check if playlist exists and belongs to user
    if not await playlists_repo.playlist_exists(user_id, playlist_id):
        raise NotFoundException("Playlist", str(playlist_id))

    # Remove track
    removed = await playlists_repo.remove_track_from_playlist(user_id, playlist_id, track_id)
    if not removed:
        raise NotFoundException("Track in playlist", str(track_id))
    return OperationResult(success=True, message="Track removed from playlist")
