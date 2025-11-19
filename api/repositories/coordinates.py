from typing import Dict, List, Optional

import asyncpg

from api.core.config import settings
from api.repositories.database import DatabaseClient, validate_table_name


class CoordinatesRepository:
    """Repository for 3D coordinate point cloud operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.db = DatabaseClient(pool)
        validate_table_name(settings.TRACK_VIZ_TABLE)
        validate_table_name(settings.MUSIC_TABLE)
        self.viz_table = settings.TRACK_VIZ_TABLE
        self.music_table = settings.MUSIC_TABLE

    async def get_all_points(self, limit: int, offset: int) -> List[Dict]:
        """Get visualization points with track metadata."""
        query = f"""
            SELECT 
                tv.id, tv.x, tv.y, tv.z, tv.cluster, tv.cluster_color,
                m.title, m.artist, m.album, m.genre, m.year
            FROM {self.viz_table} tv
            JOIN {self.music_table} m ON tv.id = m.id
            ORDER BY tv.id
            LIMIT $1 OFFSET $2;
        """
        rows = await self.db.fetch(query, limit, offset)
        return [dict(row) for row in rows]

    async def count_points(self) -> int:
        """Get total count of visualization points."""
        query = f"SELECT COUNT(*) FROM {self.viz_table};"
        result = await self.db.fetchval(query)
        return result or 0

    async def get_statistics(self) -> Dict:
        """Get overall visualization statistics."""
        # Total tracks
        total_query = f"SELECT COUNT(*) FROM {self.viz_table};"
        total = await self.db.fetchval(total_query)

        # Total clusters
        cluster_query = f"SELECT COUNT(DISTINCT cluster) FROM {self.viz_table};"
        cluster_count = await self.db.fetchval(cluster_query)

        # Genre distribution (top 10)
        genre_query = f"""
            SELECT m.genre, COUNT(*) as count
            FROM {self.viz_table} tv
            JOIN {self.music_table} m ON tv.id = m.id
            WHERE m.genre IS NOT NULL
            GROUP BY m.genre
            ORDER BY count DESC
            LIMIT 10;
        """
        genre_rows = await self.db.fetch(genre_query)

        # Largest cluster
        largest_query = f"""
            SELECT cluster, COUNT(*) as size
            FROM {self.viz_table}
            GROUP BY cluster
            ORDER BY size DESC
            LIMIT 1;
        """
        largest = await self.db.fetchrow(largest_query)

        return {
            "total_tracks": total or 0,
            "total_clusters": cluster_count or 0,
            "genre_distribution": [dict(row) for row in genre_rows],
            "largest_cluster": largest["cluster"] if largest else None,
            "largest_cluster_size": largest["size"] if largest else None,
        }

    async def search_tracks(self, query: str, limit: int) -> List[Dict]:
        """Search tracks by title, artist, album, or genre."""
        search_query = f"""
            SELECT 
                tv.id, tv.x, tv.y, tv.z, tv.cluster, tv.cluster_color,
                m.title, m.artist, m.album, m.genre, m.year
            FROM {self.viz_table} tv
            JOIN {self.music_table} m ON tv.id = m.id
            WHERE 
                LOWER(m.title) LIKE LOWER($1) OR
                LOWER(m.artist) LIKE LOWER($1) OR
                LOWER(m.album) LIKE LOWER($1) OR
                LOWER(m.genre) LIKE LOWER($1)
            ORDER BY m.title
            LIMIT $2;
        """
        search_pattern = f"%{query}%"
        rows = await self.db.fetch(search_query, search_pattern, limit)
        return [dict(row) for row in rows]

    async def get_cluster_tracks(self, cluster_id: int) -> Optional[Dict]:
        """Get all tracks in a specific cluster."""
        query = f"""
            SELECT 
                tv.id, tv.x, tv.y, tv.z, tv.cluster, tv.cluster_color,
                m.title, m.artist, m.album, m.genre, m.year
            FROM {self.viz_table} tv
            JOIN {self.music_table} m ON tv.id = m.id
            WHERE tv.cluster = $1
            ORDER BY m.artist, m.album, m.title;
        """
        rows = await self.db.fetch(query, cluster_id)
        if not rows:
            return None

        tracks = [dict(row) for row in rows]
        return {
            "cluster_id": cluster_id,
            "color": tracks[0]["cluster_color"] if tracks else None,
            "track_count": len(tracks),
            "tracks": tracks,
        }

    async def get_track_neighbors(self, track_id: int, limit: int) -> Optional[List[Dict]]:
        """Get nearest neighbors of a track in 3D space using Euclidean distance."""
        # Check if track exists
        exists_query = f"SELECT id FROM {self.viz_table} WHERE id = $1;"
        exists = await self.db.fetchval(exists_query, track_id)
        if not exists:
            return None

        query = f"""
            WITH target AS (
                SELECT x, y, z FROM {self.viz_table} WHERE id = $1
            )
            SELECT 
                tv.id, tv.x, tv.y, tv.z, tv.cluster, tv.cluster_color,
                m.title, m.artist, m.album, m.genre, m.year,
                SQRT(
                    POWER(tv.x - target.x, 2) + 
                    POWER(tv.y - target.y, 2) + 
                    POWER(tv.z - target.z, 2)
                ) as distance
            FROM {self.viz_table} tv
            JOIN {self.music_table} m ON tv.id = m.id
            CROSS JOIN target
            WHERE tv.id != $1
            ORDER BY distance
            LIMIT $2;
        """
        rows = await self.db.fetch(query, track_id, limit)
        return [dict(row) for row in rows]
