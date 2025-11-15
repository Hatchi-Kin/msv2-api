from fastapi import HTTPException
from api.repositories.music_repo import MusicRepository
from api.models.music import ArtistList, AlbumList


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
