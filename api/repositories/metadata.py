from typing import Optional

import asyncpg

from api.core.config import settings
from api.core.logger import logger
from api.models.metadata import Track, TrackList
from api.repositories.database import DatabaseClient, validate_table_name


class MetadataRepository:
    """Repository for music metadata operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.db = DatabaseClient(pool)
        validate_table_name(settings.MUSIC_TABLE)
        self.table = settings.MUSIC_TABLE

    def _get_columns(self, include_embeddings: bool = False) -> str:
        """Get column list based on whether embeddings are needed."""
        if include_embeddings:
            return "*"
        return """id, filename, filepath, relative_path, album_folder, artist_folder, 
                  filesize, title, artist, album, year, tracknumber, genre, 
                  top_5_genres, created_at"""

    async def count_tracks(self) -> int:
        query = f"SELECT COUNT(*) FROM {self.table};"
        result = await self.db.fetchval(query)
        return result or 0

    async def get_random_track(self, include_embeddings: bool = False) -> Optional[Track]:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM {self.table} ORDER BY RANDOM() LIMIT 1;"
        row = await self.db.fetchrow(query)
        return Track(**dict(row)) if row else None

    async def get_track_by_id(
        self, track_id: int, include_embeddings: bool = False
    ) -> Optional[Track]:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM {self.table} WHERE id = $1;"
        row = await self.db.fetchrow(query, track_id)
        return Track(**dict(row)) if row else None

    async def get_artist_list(self, limit: int, offset: int) -> list[str]:
        """Get paginated list of artists."""
        query = f"SELECT DISTINCT artist_folder FROM {self.table} ORDER BY artist_folder LIMIT $1 OFFSET $2;"
        rows = await self.db.fetch(query, limit, offset)
        return [row["artist_folder"] for row in rows if row["artist_folder"]]

    async def get_artist_count(self) -> int:
        query = f"SELECT COUNT(DISTINCT artist_folder) FROM {self.table};"
        result = await self.db.fetchval(query)
        return result or 0

    async def get_album_list_from_artist(self, artist_name: str) -> list[str]:
        query = f"SELECT DISTINCT album_folder FROM {self.table} WHERE artist_folder = $1;"
        rows = await self.db.fetch(query, artist_name)
        return [row["album_folder"] for row in rows if row["album_folder"]]

    async def get_tracklist_from_album(
        self, album_name: str, include_embeddings: bool = False
    ) -> TrackList:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM {self.table} WHERE album_folder = $1 ORDER BY tracknumber;"
        rows = await self.db.fetch(query, album_name)
        tracks = [Track(**dict(row)) for row in rows]
        return TrackList(tracks=tracks)

    async def get_tracklist_from_artist_and_album(
        self, artist_name: str, album_name: str, include_embeddings: bool = False
    ) -> TrackList:
        columns = self._get_columns(include_embeddings)
        query = f"SELECT {columns} FROM {self.table} WHERE artist_folder = $1 AND album = $2;"
        rows = await self.db.fetch(query, artist_name, album_name)
        tracks = [Track(**dict(row)) for row in rows]
        return TrackList(tracks=tracks)

    async def get_similar_tracks(self, track_id: int, limit: int) -> list[tuple[Track, float]]:
        """
        Get similar tracks using pgvector cosine distance.

        Args:
            track_id: ID of the track to find similar tracks for
            limit: Number of similar tracks to return

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
        rows = await self.db.fetch(query, track_id, limit)
        results = []
        for row in rows:
            row_dict = dict(row)
            distance = row_dict.pop("distance")
            track = Track(**row_dict)
            results.append((track, float(distance)))

        logger.debug(f"Found {len(results)} similar tracks for track {track_id}")
        return results
