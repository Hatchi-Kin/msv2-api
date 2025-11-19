import asyncpg

from api.core.config import settings
from api.core.logger import logger
from api.models.metadata import Track
from api.repositories.database import DatabaseClient, validate_table_name


class FavoritesRepository:
    """Repository for user favorites operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.db = DatabaseClient(pool)
        validate_table_name(settings.FAVORITES_TABLE)
        validate_table_name(settings.MUSIC_TABLE)
        self.favorites_table = settings.FAVORITES_TABLE
        self.music_table = settings.MUSIC_TABLE

    async def get_favorites_count(self, user_id: int) -> int:
        """Get count of user's favorites."""
        query = f"SELECT COUNT(*) FROM {self.favorites_table} WHERE user_id = $1;"
        return await self.db.fetchval(query, user_id) or 0

    async def track_exists(self, track_id: int) -> bool:
        """Check if track exists in music table."""
        query = f"SELECT id FROM {self.music_table} WHERE id = $1;"
        result = await self.db.fetchval(query, track_id)
        return result is not None

    async def add_favorite(self, user_id: int, track_id: int) -> bool:
        """Add a track to user's favorites. Returns True if added, False if already exists."""
        query = f"""
            INSERT INTO {self.favorites_table} (user_id, track_id) 
            VALUES ($1, $2) 
            ON CONFLICT DO NOTHING 
            RETURNING id;
        """
        result = await self.db.fetchval(query, user_id, track_id)
        if result:
            logger.info(f"User {user_id} added track {track_id} to favorites")
        return result is not None

    async def remove_favorite(self, user_id: int, track_id: int) -> bool:
        """Remove a track from user's favorites. Returns True if removed."""
        query = (
            f"DELETE FROM {self.favorites_table} WHERE user_id = $1 AND track_id = $2 RETURNING id;"
        )
        result = await self.db.fetchval(query, user_id, track_id)
        if result:
            logger.info(f"User {user_id} removed track {track_id} from favorites")
        return result is not None

    async def get_user_favorites(self, user_id: int) -> tuple[list[Track], int]:
        """Get all favorite tracks for a user."""
        query = f"""
            SELECT m.*, f.created_at as favorited_at
            FROM {self.favorites_table} f
            JOIN {self.music_table} m ON f.track_id = m.id
            WHERE f.user_id = $1
            ORDER BY f.created_at DESC;
        """
        rows = await self.db.fetch(query, user_id)
        tracks = [Track(**dict(row)) for row in rows]
        count = await self.get_favorites_count(user_id)
        return tracks, count

    async def is_favorite(self, user_id: int, track_id: int) -> bool:
        """Check if a track is in user's favorites."""
        query = f"SELECT id FROM {self.favorites_table} WHERE user_id = $1 AND track_id = $2;"
        result = await self.db.fetchval(query, user_id, track_id)
        return result is not None
