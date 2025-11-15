from fastapi import HTTPException
from api.connectors.postgres_connector import PostgresConnector


async def get_song_count_handler(db_connector: PostgresConnector) -> int:
    count = await db_connector.count_songs()
    if count is None:
        raise HTTPException(status_code=404, detail="Could not retrieve song count.")
    return count


async def get_random_song_handler(include_embeddings: bool, db_connector: PostgresConnector):
    song = await db_connector.get_random_song(include_embeddings)
    if not song:
        raise HTTPException(status_code=404, detail="No songs found")
    return song


async def get_song_by_id_handler(song_id: int, include_embeddings: bool, db_connector: PostgresConnector):
    song = await db_connector.get_song_by_id(song_id, include_embeddings)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found.")
    return song


async def get_artist_list_handler(db_connector: PostgresConnector):
    artists = await db_connector.get_artist_list()
    if not artists:
        raise HTTPException(status_code=404, detail="No artists found in the database.")
    return artists


async def get_album_list_from_artist_handler(artist_name: str, db_connector: PostgresConnector):
    albums = await db_connector.get_album_list_from_artist(artist_name)
    if not albums:
        raise HTTPException(status_code=404, detail="No albums found for the given artist.")
    return albums


async def get_tracklist_from_album_handler(
    album_name: str, include_embeddings: bool, db_connector: PostgresConnector
):
    tracks = await db_connector.get_tracklist_from_album(album_name, include_embeddings)
    if not tracks:
        raise HTTPException(status_code=404, detail="No tracks found for the given album.")
    return tracks


async def get_tracklist_from_artist_and_album_handler(
    artist_name: str, album_name: str, include_embeddings: bool, db_connector: PostgresConnector
):
    tracklist = await db_connector.get_tracklist_from_artist_and_album(
        artist_name, album_name, include_embeddings
    )
    if not tracklist:
        raise HTTPException(status_code=404, detail="No tracks found for the given artist and album.")
    return tracklist
