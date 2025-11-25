from typing import Optional

import asyncpg

from api.core.config import settings
from api.core.logger import logger
from api.models.library import Track
from api.repositories.database import DatabaseClient, validate_table_name


class PlaylistsRepository:
    """Repository for user playlists operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.db = DatabaseClient(pool)
        validate_table_name(settings.PLAYLISTS_TABLE)
        validate_table_name(settings.PLAYLIST_TRACKS_TABLE)
        validate_table_name(settings.MUSIC_TABLE)
        self.playlists_table = settings.PLAYLISTS_TABLE
        self.playlist_tracks_table = settings.PLAYLIST_TRACKS_TABLE
        self.music_table = settings.MUSIC_TABLE

    async def playlist_exists(self, user_id: int, playlist_id: int) -> bool:
        """Check if playlist exists and belongs to user."""
        query = f"SELECT id FROM {self.playlists_table} WHERE id = $1 AND user_id = $2;"
        result = await self.db.fetchval(query, playlist_id, user_id)
        return result is not None

    async def track_exists(self, track_id: int) -> bool:
        """Check if track exists in music table."""
        query = f"SELECT id FROM {self.music_table} WHERE id = $1;"
        result = await self.db.fetchval(query, track_id)
        return result is not None

    async def get_playlist_track_count(self, playlist_id: int) -> int:
        """Get count of tracks in playlist."""
        query = (
            f"SELECT COUNT(*) FROM {self.playlist_tracks_table} WHERE playlist_id = $1;"
        )
        return await self.db.fetchval(query, playlist_id) or 0

    async def create_playlist(self, user_id: int, name: str) -> dict:
        """Create a new playlist."""
        query = f"""
            INSERT INTO {self.playlists_table} (user_id, name) 
            VALUES ($1, $2) 
            RETURNING id, name, created_at, updated_at;
        """
        row = await self.db.fetchrow(query, user_id, name)
        logger.info(f"User {user_id} created playlist: {name}")
        return {
            "id": row["id"],
            "name": row["name"],
            "track_count": 0,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    async def get_user_playlists(self, user_id: int) -> list[dict]:
        """Get all playlists for a user."""
        query = f"""
            SELECT 
                p.id, p.name, p.created_at, p.updated_at,
                COUNT(pt.id) as track_count
            FROM {self.playlists_table} p
            LEFT JOIN {self.playlist_tracks_table} pt ON p.id = pt.playlist_id
            WHERE p.user_id = $1
            GROUP BY p.id, p.name, p.created_at, p.updated_at
            ORDER BY p.updated_at DESC;
        """
        rows = await self.db.fetch(query, user_id)
        return [dict(row) for row in rows]

    async def get_playlist_detail(
        self, user_id: int, playlist_id: int
    ) -> Optional[dict]:
        """Get playlist with all tracks. Returns None if not found."""
        # Get playlist info
        playlist_query = f"""
            SELECT id, name, created_at, updated_at 
            FROM {self.playlists_table} 
            WHERE id = $1 AND user_id = $2;
        """
        playlist = await self.db.fetchrow(playlist_query, playlist_id, user_id)
        if not playlist:
            return None

        # Get tracks
        tracks_query = f"""
            SELECT m.*, pt.position, pt.added_at
            FROM {self.playlist_tracks_table} pt
            JOIN {self.music_table} m ON pt.track_id = m.id
            WHERE pt.playlist_id = $1
            ORDER BY pt.position;
        """
        rows = await self.db.fetch(tracks_query, playlist_id)
        tracks = [Track(**dict(row)) for row in rows]

        return {
            "id": playlist["id"],
            "name": playlist["name"],
            "tracks": tracks,
            "created_at": playlist["created_at"],
            "updated_at": playlist["updated_at"],
        }

    async def update_playlist_name(
        self, user_id: int, playlist_id: int, new_name: str
    ) -> bool:
        """Update playlist name. Returns True if updated, False if not found."""
        query = f"""
            UPDATE {self.playlists_table} 
            SET name = $1, updated_at = NOW() 
            WHERE id = $2 AND user_id = $3 
            RETURNING id;
        """
        result = await self.db.fetchval(query, new_name, playlist_id, user_id)
        if result:
            logger.info(f"User {user_id} renamed playlist {playlist_id} to: {new_name}")
        return result is not None

    async def delete_playlist(self, user_id: int, playlist_id: int) -> bool:
        """Delete a playlist. Returns True if deleted, False if not found."""
        query = f"DELETE FROM {self.playlists_table} WHERE id = $1 AND user_id = $2 RETURNING id;"
        result = await self.db.fetchval(query, playlist_id, user_id)
        if result:
            logger.info(f"User {user_id} deleted playlist {playlist_id}")
        return result is not None

    async def add_track_to_playlist(
        self, user_id: int, playlist_id: int, track_id: int
    ) -> bool:
        """Add track to playlist. Returns True if added, False if already exists."""

        # We access the pool directly to ensure all steps happen in ONE transaction.
        # If step 3 fails, step 2 is rolled back automatically.
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                # 1. Get next position
                next_pos_query = f"""
                        SELECT COALESCE(MAX(position), 0) + 1 
                        FROM {self.playlist_tracks_table} 
                        WHERE playlist_id = $1;
                    """
                next_pos = await conn.fetchval(next_pos_query, playlist_id)

                # 2. Add track
                add_query = f"""
                        INSERT INTO {self.playlist_tracks_table} (playlist_id, track_id, position) 
                        VALUES ($1, $2, $3) 
                        ON CONFLICT DO NOTHING 
                        RETURNING id;
                    """
                result = await conn.fetchval(add_query, playlist_id, track_id, next_pos)

                # 3. Update playlist timestamp (Only if insert succeeded)
                if result:
                    update_query = f"UPDATE {self.playlists_table} SET updated_at = NOW() WHERE id = $1;"
                    await conn.execute(update_query, playlist_id)
                    logger.info(f"Added track {track_id} to playlist {playlist_id}")

                return result is not None

    async def remove_track_from_playlist(
        self, user_id: int, playlist_id: int, track_id: int
    ) -> bool:
        """Remove track from playlist. Returns True if removed."""
        # Get position of track to remove
        position_query = f"""
            SELECT position 
            FROM {self.playlist_tracks_table} 
            WHERE playlist_id = $1 AND track_id = $2;
        """
        position = await self.db.fetchval(position_query, playlist_id, track_id)
        if position is None:
            return False

        # Delete track
        delete_query = f"""
            DELETE FROM {self.playlist_tracks_table} 
            WHERE playlist_id = $1 AND track_id = $2;
        """
        await self.db.execute(delete_query, playlist_id, track_id)

        # Reorder remaining tracks
        reorder_query = f"""
            UPDATE {self.playlist_tracks_table} 
            SET position = position - 1 
            WHERE playlist_id = $1 AND position > $2;
        """
        await self.db.execute(reorder_query, playlist_id, position)

        # Update playlist timestamp
        update_query = (
            f"UPDATE {self.playlists_table} SET updated_at = NOW() WHERE id = $1;"
        )
        await self.db.execute(update_query, playlist_id)

        logger.info(f"Removed track {track_id} from playlist {playlist_id}")
        return True
