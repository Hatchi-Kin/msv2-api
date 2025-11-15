from typing import Optional

import asyncpg

from api.models.music import MegasetTrack, TrackList


class MusicRepository:
    """Repository for music metadata operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    def _get_columns(self, include_embeddings: bool = False) -> str:
        """Get column list based on whether embeddings are needed."""
        if include_embeddings:
            return "*"
        return """id, filename, filepath, relative_path, album_folder, artist_folder, 
                  filesize, title, artist, album, year, tracknumber, genre, 
                  top_5_genres, created_at"""

    async def count_songs(self) -> int:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM megaset;")
            return result or 0

    async def get_random_song(self, include_embeddings: bool = False) -> Optional[MegasetTrack]:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM megaset ORDER BY RANDOM() LIMIT 1;"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return MegasetTrack(**dict(row)) if row else None

    async def get_song_by_id(self, song_id: int, include_embeddings: bool = False) -> Optional[MegasetTrack]:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM megaset WHERE id = $1;"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, song_id)
            return MegasetTrack(**dict(row)) if row else None

    async def get_artist_list(self) -> list[str]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT artist_folder FROM megaset;")
            return [row["artist_folder"] for row in rows if row["artist_folder"]]

    async def get_album_list_from_artist(self, artist_name: str) -> list[str]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT album_folder FROM megaset WHERE artist_folder = $1;",
                artist_name,
            )
            return [row["album_folder"] for row in rows if row["album_folder"]]

    async def get_tracklist_from_album(self, album_name: str, include_embeddings: bool = False) -> TrackList:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM megaset WHERE album_folder = $1;"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, album_name)
            tracks = [MegasetTrack(**dict(row)) for row in rows]
            return TrackList(tracks=tracks)

    async def get_tracklist_from_artist_and_album(
        self, artist_name: str, album_name: str, include_embeddings: bool = False
    ) -> TrackList:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM megaset WHERE artist_folder = $1 AND album = $2;"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, artist_name, album_name)
            tracks = [MegasetTrack(**dict(row)) for row in rows]
            return TrackList(tracks=tracks)
