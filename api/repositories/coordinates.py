from typing import Dict, List, Optional

import asyncpg

from api.core.config import settings
from api.models.coordinates import VisualizationType
from api.repositories.database import DatabaseClient, validate_table_name


class CoordinatesRepository:
    """Repository for 3D coordinate point cloud operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.db = DatabaseClient(pool)
        validate_table_name(settings.TRACK_VIZ_TABLE)
        validate_table_name(settings.TRACK_VIZ_TABLE_2)
        validate_table_name(settings.MUSIC_TABLE)
        self.viz_table = settings.TRACK_VIZ_TABLE
        self.viz_table_umap = settings.TRACK_VIZ_TABLE_2
        self.viz_table_sphere = settings.TRACK_VIZ_TABLE_3
        self.music_table = settings.MUSIC_TABLE

    def _get_table(self, viz_type: VisualizationType) -> str:
        """Get the table name based on visualization type."""
        if viz_type == VisualizationType.UMAP:
            return self.viz_table_umap
        if viz_type == VisualizationType.SPHERE:
            return self.viz_table_sphere
        return self.viz_table

    async def get_all_points(
        self,
        limit: int,
        offset: int,
        viz_type: VisualizationType = VisualizationType.DEFAULT,
    ) -> List[Dict]:
        """Get visualization points with track metadata."""
        table = self._get_table(viz_type)
        query = f"""
            SELECT 
                tv.id, tv.x, tv.y, tv.z, tv.cluster, tv.cluster_color,
                m.title, m.artist, m.album, m.genre, m.year
            FROM {table} tv
            JOIN {self.music_table} m ON tv.id = m.id
            ORDER BY tv.id
            LIMIT $1 OFFSET $2;
        """
        rows = await self.db.fetch(query, limit, offset)
        return [dict(row) for row in rows]

    async def count_points(
        self, viz_type: VisualizationType = VisualizationType.DEFAULT
    ) -> int:
        """Get total count of visualization points."""
        table = self._get_table(viz_type)
        query = f"SELECT COUNT(*) FROM {table};"
        result = await self.db.fetchval(query)
        return result or 0

    async def get_statistics(
        self, viz_type: VisualizationType = VisualizationType.DEFAULT
    ) -> Dict:
        """Get overall visualization statistics."""
        table = self._get_table(viz_type)
        # Total tracks
        total_query = f"SELECT COUNT(*) FROM {table};"
        total = await self.db.fetchval(total_query)

        # Total clusters
        cluster_query = f"SELECT COUNT(DISTINCT cluster) FROM {table};"
        cluster_count = await self.db.fetchval(cluster_query)

        # Genre distribution (top 10)
        genre_query = f"""
            SELECT m.genre, COUNT(*) as count
            FROM {table} tv
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
            FROM {table}
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

    async def search_tracks(
        self,
        query: str,
        limit: int,
        viz_type: VisualizationType = VisualizationType.DEFAULT,
    ) -> List[Dict]:
        """Search tracks by title, artist, album, or genre."""
        table = self._get_table(viz_type)
        search_query = f"""
            SELECT 
                tv.id, tv.x, tv.y, tv.z, tv.cluster, tv.cluster_color,
                m.title, m.artist, m.album, m.genre, m.year
            FROM {table} tv
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

    async def get_cluster_tracks(
        self, cluster_id: int, viz_type: VisualizationType = VisualizationType.DEFAULT
    ) -> Optional[Dict]:
        """Get all tracks in a specific cluster."""
        table = self._get_table(viz_type)
        query = f"""
            SELECT 
                tv.id, tv.x, tv.y, tv.z, tv.cluster, tv.cluster_color,
                m.title, m.artist, m.album, m.genre, m.year
            FROM {table} tv
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

    async def get_track_neighbors(
        self,
        track_id: int,
        limit: int,
        viz_type: VisualizationType = VisualizationType.DEFAULT,
    ) -> Optional[List[Dict]]:
        """Get nearest neighbors of a track in 3D space using Euclidean distance."""
        table = self._get_table(viz_type)
        # Check if track exists
        exists_query = f"SELECT id FROM {table} WHERE id = $1;"
        exists = await self.db.fetchval(exists_query, track_id)
        if not exists:
            return None

        query = f"""
            WITH target AS (
                SELECT x, y, z FROM {table} WHERE id = $1
            )
            SELECT 
                tv.id, tv.x, tv.y, tv.z, tv.cluster, tv.cluster_color,
                m.title, m.artist, m.album, m.genre, m.year,
                SQRT(
                    POWER(tv.x - target.x, 2) + 
                    POWER(tv.y - target.y, 2) + 
                    POWER(tv.z - target.z, 2)
                ) as distance
            FROM {table} tv
            JOIN {self.music_table} m ON tv.id = m.id
            CROSS JOIN target
            WHERE tv.id != $1
            ORDER BY distance
            LIMIT $2;
        """
        rows = await self.db.fetch(query, track_id, limit)
        return [dict(row) for row in rows]
