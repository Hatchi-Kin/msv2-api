from typing import Optional

import asyncpg

from api.models.music_db import MegasetTrack, TrackList
from api.core.config import settings


class MusicRepository:
    """Repository for music metadata operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.table = settings.MUSIC_TABLE

    def _get_columns(self, include_embeddings: bool = False) -> str:
        """Get column list based on whether embeddings are needed."""
        if include_embeddings:
            return "*"
        return """id, filename, filepath, relative_path, album_folder, artist_folder, 
                  filesize, title, artist, album, year, tracknumber, genre, 
                  top_5_genres, created_at"""

    async def count_tracks(self) -> int:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table};")
            return result or 0

    async def get_random_track(self, include_embeddings: bool = False) -> Optional[MegasetTrack]:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM {self.table} ORDER BY RANDOM() LIMIT 1;"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return MegasetTrack(**dict(row)) if row else None

    async def get_track_by_id(
        self, track_id: int, include_embeddings: bool = False
    ) -> Optional[MegasetTrack]:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM {self.table} WHERE id = $1;"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, track_id)
            return MegasetTrack(**dict(row)) if row else None

    async def get_artist_list(self, limit: int = 100, offset: int = 0) -> list[str]:
        """Get paginated list of artists."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT DISTINCT artist_folder FROM {self.table} ORDER BY artist_folder LIMIT $1 OFFSET $2;",
                limit,
                offset,
            )
            return [row["artist_folder"] for row in rows if row["artist_folder"]]

    async def get_artist_count(self) -> int:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(f"SELECT COUNT(DISTINCT artist_folder) FROM {self.table};")
            return result or 0

    async def get_album_list_from_artist(self, artist_name: str) -> list[str]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT DISTINCT album_folder FROM {self.table} WHERE artist_folder = $1;",
                artist_name,
            )
            return [row["album_folder"] for row in rows if row["album_folder"]]

    async def get_tracklist_from_album(self, album_name: str, include_embeddings: bool = False) -> TrackList:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM {self.table} WHERE album_folder = $1 ORDER BY tracknumber;"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, album_name)
            tracks = [MegasetTrack(**dict(row)) for row in rows]
        return TrackList(tracks=tracks)

    async def get_tracklist_from_artist_and_album(
        self, artist_name: str, album_name: str, include_embeddings: bool = False
    ) -> TrackList:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM {self.table} WHERE artist_folder = $1 AND album = $2;"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, artist_name, album_name)
            tracks = [MegasetTrack(**dict(row)) for row in rows]
            return TrackList(tracks=tracks)

    async def get_similar_tracks(self, track_id: int, limit: int = 30) -> list[tuple[MegasetTrack, float]]:
        """
        Get similar tracks using pgvector cosine distance.

        Args:
            track_id: ID of the track to find similar tracks for
            limit: Number of similar tracks to return (default 30 to allow for artist diversity filtering)

        Returns:
            List of tuples: (track, distance_score)
        """
        query = f"""
            WITH target AS (
                SELECT embedding_512_vector 
                FROM {self.table} 
                WHERE id = $1
            )
            SELECT 
                m.id, m.filename, m.filepath, m.relative_path, m.album_folder, 
                m.artist_folder, m.filesize, m.title, m.artist, m.album, 
                m.year, m.tracknumber, m.genre, m.top_5_genres, m.created_at,
                (m.embedding_512_vector <=> (SELECT embedding_512_vector FROM target)) as distance
            FROM {self.table} m, target
            WHERE m.id != $1 
                AND m.embedding_512_vector IS NOT NULL
                AND (SELECT embedding_512_vector FROM target) IS NOT NULL
            ORDER BY distance
            LIMIT $2;
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, track_id, limit)
            results = []
            for row in rows:
                row_dict = dict(row)
                distance = row_dict.pop("distance")
                track = MegasetTrack(**row_dict)
                results.append((track, float(distance)))
            return results
