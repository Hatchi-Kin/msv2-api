from fastapi import HTTPException

from api.repositories.music_repo import MusicRepository
from api.models.music import ArtistList, AlbumList, SimilarTrack, SimilarTrackList


async def get_song_count_handler(music_repo: MusicRepository) -> int:
    count = await music_repo.count_songs()
    if count is None:
        raise HTTPException(status_code=404, detail="Could not retrieve song count.")
    return count


async def get_random_song_handler(include_embeddings: bool, music_repo: MusicRepository):
    song = await music_repo.get_random_song(include_embeddings)
    if not song:
        raise HTTPException(status_code=404, detail="No songs found")
    return song


async def get_song_by_id_handler(song_id: int, include_embeddings: bool, music_repo: MusicRepository):
    song = await music_repo.get_song_by_id(song_id, include_embeddings)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found.")
    return song


async def get_artist_list_handler(music_repo: MusicRepository):
    artists = await music_repo.get_artist_list()
    if not artists:
        raise HTTPException(status_code=404, detail="No artists found in the database.")
    return ArtistList(artists=artists)


async def get_album_list_from_artist_handler(artist_name: str, music_repo: MusicRepository):
    albums = await music_repo.get_album_list_from_artist(artist_name)
    if not albums:
        raise HTTPException(status_code=404, detail="No albums found for the given artist.")
    return AlbumList(albums=albums)


async def get_tracklist_from_album_handler(
    album_name: str, include_embeddings: bool, music_repo: MusicRepository
):
    tracks = await music_repo.get_tracklist_from_album(album_name, include_embeddings)
    if not tracks.tracks:
        raise HTTPException(status_code=404, detail="No tracks found for the given album.")
    return tracks


async def get_tracklist_from_artist_and_album_handler(
    artist_name: str, album_name: str, include_embeddings: bool, music_repo: MusicRepository
):
    tracklist = await music_repo.get_tracklist_from_artist_and_album(
        artist_name, album_name, include_embeddings
    )
    if not tracklist.tracks:
        raise HTTPException(status_code=404, detail="No tracks found for the given artist and album.")
    return tracklist


async def get_similar_tracks_handler(track_id: int, music_repo: MusicRepository) -> SimilarTrackList:
    """
    Get 9 similar tracks with artist diversity filtering.
    Queries for 30 similar tracks, then filters to max 1 per artist.
    """
    # Get the original track to exclude its artist from recommendations
    original_track = await music_repo.get_song_by_id(track_id, include_embeddings=False)
    if not original_track:
        raise HTTPException(status_code=404, detail="Track not found.")
    
    # Get 30 similar tracks from pgvector
    similar_tracks = await music_repo.get_similar_tracks(track_id, limit=30)
    
    if not similar_tracks:
        raise HTTPException(status_code=404, detail="No similar tracks found.")
    
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
        
        if len(filtered_tracks) == 9:
            break
    
    # If we don't have 9 unique artists, fill with fallback tracks
    if len(filtered_tracks) < 9:
        filtered_tracks.extend(fallback_tracks[:9 - len(filtered_tracks)])
    
    return SimilarTrackList(tracks=filtered_tracks)
