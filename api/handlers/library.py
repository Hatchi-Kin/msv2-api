from api.core.config import settings
from api.core.exceptions import NotFoundException
from api.core.logger import logger
from api.models.library import (
    AlbumList,
    ArtistList,
    SimilarTrack,
    SimilarTrackList,
    Track,
    TrackList,
)
from api.repositories.library import LibraryRepository


async def get_track_count_handler(library_repo: LibraryRepository) -> int:
    return await library_repo.count_tracks()


async def get_random_track_handler(
    library_repo: LibraryRepository, include_embeddings: bool = False
) -> Track:
    track = await library_repo.get_random_track(include_embeddings)
    if not track:
        raise NotFoundException("Track")
    return track


async def get_track_by_id_handler(
    track_id: int, library_repo: LibraryRepository, include_embeddings: bool = False
) -> Track:
    track = await library_repo.get_track_by_id(track_id, include_embeddings)
    if not track:
        raise NotFoundException("Track", str(track_id))
    return track


async def get_artist_list_handler(
    library_repo: LibraryRepository, limit: int, offset: int
) -> ArtistList:
    artists = await library_repo.get_artist_list(limit, offset)
    total = await library_repo.get_artist_count()
    if not artists:
        raise NotFoundException("Artists")
    return ArtistList(artists=artists, total=total)


async def get_album_list_from_artist_handler(
    artist_name: str, library_repo: LibraryRepository
) -> AlbumList:
    albums = await library_repo.get_album_list_from_artist(artist_name)
    if not albums:
        raise NotFoundException("Albums", artist_name)
    return AlbumList(albums=albums)


async def get_tracklist_from_album_handler(
    album_name: str, library_repo: LibraryRepository, include_embeddings: bool = False
) -> TrackList:
    tracks = await library_repo.get_tracklist_from_album(album_name, include_embeddings)
    if not tracks.tracks:
        raise NotFoundException("Tracks", album_name)
    return tracks


async def get_tracklist_from_artist_and_album_handler(
    artist_name: str,
    album_name: str,
    library_repo: LibraryRepository,
    include_embeddings: bool = False,
) -> TrackList:
    tracklist = await library_repo.get_tracklist_from_artist_and_album(
        artist_name, album_name, include_embeddings
    )
    if not tracklist.tracks:
        raise NotFoundException("Tracks", f"{artist_name}/{album_name}")
    return tracklist


async def get_similar_tracks_handler(
    track_id: int, library_repo: LibraryRepository
) -> SimilarTrackList:
    # Get the original track to exclude its artist from recommendations
    original_track = await library_repo.get_track_by_id(track_id, include_embeddings=False)
    if not original_track:
        logger.warning(f"Similarity search requested for non-existent track: {track_id}")
        raise NotFoundException("Track", str(track_id))

    # Query for candidates to allow for artist diversity filtering
    similar_tracks = await library_repo.get_similar_tracks(
        track_id, limit=settings.SIMILAR_TRACKS_LIMIT
    )

    if not similar_tracks:
        logger.warning(f"No similar tracks found for track: {track_id}")
        raise NotFoundException("Similar tracks", str(track_id))

    logger.debug(
        f"Found {len(similar_tracks)} similar tracks for '{original_track.title}' by {original_track.artist}"
    )

    # Apply artist diversity filter (max 1 track per artist)
    seen_artists = {original_track.artist} if original_track.artist else set()
    filtered_tracks = []
    fallback_tracks = []

    for track, distance in similar_tracks:
        similar_track = SimilarTrack(track=track, similarity_score=distance)

        if track.artist not in seen_artists:
            filtered_tracks.append(similar_track)
            seen_artists.add(track.artist)
        else:
            fallback_tracks.append(similar_track)

        if len(filtered_tracks) == settings.SIMILAR_TRACKS_RETURNED:
            break

    # Fill remainder with duplicate artists if needed
    if len(filtered_tracks) < settings.SIMILAR_TRACKS_RETURNED:
        filtered_tracks.extend(
            fallback_tracks[: settings.SIMILAR_TRACKS_RETURNED - len(filtered_tracks)]
        )

    return SimilarTrackList(tracks=filtered_tracks)
