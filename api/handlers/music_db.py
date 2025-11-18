from fastapi import HTTPException

from api.repositories.music_db import MusicRepository
from api.models.music_db import ArtistList, AlbumList, SimilarTrack, SimilarTrackList
from api.core.logger import logger


async def get_track_count_handler(music_repo: MusicRepository) -> int:
    count = await music_repo.count_tracks()
    if count is None:
        raise HTTPException(status_code=404, detail="Could not retrieve track count.")
    return count


async def get_random_track_handler(music_repo: MusicRepository, include_embeddings: bool = False):
    track = await music_repo.get_random_track(include_embeddings)
    if not track:
        raise HTTPException(status_code=404, detail="No tracks found")
    return track


async def get_track_by_id_handler(
    track_id: int, music_repo: MusicRepository, include_embeddings: bool = False
):
    track = await music_repo.get_track_by_id(track_id, include_embeddings)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found.")
    return track


async def get_artist_list_handler(music_repo: MusicRepository, limit: int = 100, offset: int = 0):
    artists = await music_repo.get_artist_list(limit, offset)
    count = await music_repo.get_artist_count()
    if not artists:
        raise HTTPException(status_code=404, detail="No artists found in the database.")
    return ArtistList(artists=artists, count=count)


async def get_album_list_from_artist_handler(artist_name: str, music_repo: MusicRepository):
    albums = await music_repo.get_album_list_from_artist(artist_name)
    if not albums:
        raise HTTPException(status_code=404, detail="No albums found for the given artist.")
    return AlbumList(albums=albums)


async def get_tracklist_from_album_handler(
    album_name: str, music_repo: MusicRepository, include_embeddings: bool = False
):
    tracks = await music_repo.get_tracklist_from_album(album_name, include_embeddings)
    if not tracks.tracks:
        raise HTTPException(status_code=404, detail="No tracks found for the given album.")
    return tracks


async def get_tracklist_from_artist_and_album_handler(
    artist_name: str, album_name: str, music_repo: MusicRepository, include_embeddings: bool = False
):
    tracklist = await music_repo.get_tracklist_from_artist_and_album(
        artist_name, album_name, include_embeddings
    )
    if not tracklist.tracks:
        raise HTTPException(status_code=404, detail="No tracks found for the given artist and album.")
    return tracklist


async def get_similar_tracks_handler(track_id: int, music_repo: MusicRepository) -> SimilarTrackList:
    # Get the original track to exclude its artist from recommendations
    original_track = await music_repo.get_track_by_id(track_id, include_embeddings=False)
    if not original_track:
        logger.warning(f"Similarity search requested for non-existent track ID: {track_id}")
        raise HTTPException(status_code=404, detail="Track not found.")

    # Query for 30 candidates to ensure we can filter down to 9 diverse results
    # after removing duplicate artists
    similar_tracks = await music_repo.get_similar_tracks(track_id, limit=30)

    if not similar_tracks:
        logger.warning(f"No similar tracks found for track ID: {track_id}")
        raise HTTPException(status_code=404, detail="No similar tracks found.")

    logger.debug(
        f"Found {len(similar_tracks)} similar tracks for '{original_track.title}' by {original_track.artist}"
    )

    # Apply artist diversity filter (max 1 track per artist)
    # Start with the original track's artist already in the set
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

        # Stop once we have 9 diverse recommendations
        if len(filtered_tracks) == 9:
            break

    # If we don't have 9 unique artists, fill remainder with duplicate artists
    if len(filtered_tracks) < 9:
        filtered_tracks.extend(fallback_tracks[: 9 - len(filtered_tracks)])

    return SimilarTrackList(tracks=filtered_tracks)
