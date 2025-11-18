from typing import Optional

import asyncpg

from api.models.music_db import MegasetTrack, TrackList
from api.core.config import settings


class MusicRepository:
    """Repository for music metadata operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.table = settings.MUSIC_TABLE

    # ----------------------------------------------- #

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

    # ----------------------------------------------- #

    async def add_favorite(self, user_id: int, track_id: int) -> dict:
        """Add a track to user's favorites. Returns dict with 'added' bool and optional 'error' string."""
        async with self.pool.acquire() as conn:
            # Check count
            count = await conn.fetchval("SELECT COUNT(*) FROM favorites WHERE user_id = $1;", user_id)
            if count >= 20:
                return {"added": False, "error": "max_limit"}

            # Check if track exists
            track = await self.get_track_by_id(track_id, include_embeddings=False)
            if not track:
                return {"added": False, "error": "track_not_found"}

            # Add favorite
            result = await conn.fetchval(
                "INSERT INTO favorites (user_id, track_id) VALUES ($1, $2) ON CONFLICT DO NOTHING RETURNING id;",
                user_id,
                track_id,
            )

            return {"added": result is not None, "error": None}

    async def remove_favorite(self, user_id: int, track_id: int) -> dict:
        """Remove a track from user's favorites. Returns dict with 'removed' bool."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "DELETE FROM favorites WHERE user_id = $1 AND track_id = $2 RETURNING id;", user_id, track_id
            )
            return {"removed": result is not None}

    async def get_user_favorites(self, user_id: int):
        """Get all favorite tracks for a user."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT m.*, f.created_at as favorited_at
                FROM favorites f
                JOIN {self.table} m ON f.track_id = m.id
                WHERE f.user_id = $1
                ORDER BY f.created_at DESC;
                """,
                user_id,
            )
            tracks = [MegasetTrack(**dict(row)) for row in rows]
            count = await conn.fetchval("SELECT COUNT(*) FROM favorites WHERE user_id = $1;", user_id)
            return {"tracks": tracks, "total": count or 0}

    async def check_is_favorite(self, user_id: int, track_id: int) -> bool:
        """Check if a track is in user's favorites."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT id FROM favorites WHERE user_id = $1 AND track_id = $2;", user_id, track_id
            )
            return result is not None

    # ----------------------------------------------- #

    async def create_playlist(self, user_id: int, name: str):
        """Create a new playlist."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO playlists (user_id, name) VALUES ($1, $2) RETURNING id, name, created_at, updated_at;",
                user_id,
                name,
            )
            return {
                "id": row["id"],
                "name": row["name"],
                "track_count": 0,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    async def get_user_playlists(self, user_id: int):
        """Get all playlists for a user."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    p.id, p.name, p.created_at, p.updated_at,
                    COUNT(pt.id) as track_count
                FROM playlists p
                LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
                WHERE p.user_id = $1
                GROUP BY p.id, p.name, p.created_at, p.updated_at
                ORDER BY p.updated_at DESC;
                """,
                user_id,
            )
            return [dict(row) for row in rows]

    async def get_playlist_detail(self, user_id: int, playlist_id: int) -> Optional[dict]:
        """Get playlist with all tracks. Returns None if not found."""
        async with self.pool.acquire() as conn:
            # Get playlist info
            playlist = await conn.fetchrow(
                "SELECT id, name, created_at, updated_at FROM playlists WHERE id = $1 AND user_id = $2;",
                playlist_id,
                user_id,
            )
            if not playlist:
                return None

            # Get tracks
            rows = await conn.fetch(
                f"""
                SELECT m.*, pt.position, pt.added_at
                FROM playlist_tracks pt
                JOIN {self.table} m ON pt.track_id = m.id
                WHERE pt.playlist_id = $1
                ORDER BY pt.position;
                """,
                playlist_id,
            )
            tracks = [MegasetTrack(**dict(row)) for row in rows]

            return {
                "id": playlist["id"],
                "name": playlist["name"],
                "tracks": tracks,
                "created_at": playlist["created_at"],
                "updated_at": playlist["updated_at"],
            }

    async def update_playlist_name(self, user_id: int, playlist_id: int, new_name: str) -> bool:
        """Update playlist name. Returns True if updated, False if not found."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "UPDATE playlists SET name = $1, updated_at = NOW() WHERE id = $2 AND user_id = $3 RETURNING id;",
                new_name,
                playlist_id,
                user_id,
            )
            return result is not None

    async def delete_playlist(self, user_id: int, playlist_id: int) -> bool:
        """Delete a playlist. Returns True if deleted, False if not found."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "DELETE FROM playlists WHERE id = $1 AND user_id = $2 RETURNING id;", playlist_id, user_id
            )
            return result is not None

    async def add_track_to_playlist(self, user_id: int, playlist_id: int, track_id: int) -> dict:
        """Add track to playlist. Returns dict with 'added' bool and optional 'error' string."""
        async with self.pool.acquire() as conn:
            # Verify playlist belongs to user
            playlist = await conn.fetchval(
                "SELECT id FROM playlists WHERE id = $1 AND user_id = $2;", playlist_id, user_id
            )
            if not playlist:
                return {"added": False, "error": "playlist_not_found"}

            # Check track count
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = $1;", playlist_id
            )
            if count >= 20:
                return {"added": False, "error": "max_limit"}

            # Check if track exists
            track = await self.get_track_by_id(track_id, include_embeddings=False)
            if not track:
                return {"added": False, "error": "track_not_found"}

            # Get next position
            next_pos = await conn.fetchval(
                "SELECT COALESCE(MAX(position), 0) + 1 FROM playlist_tracks WHERE playlist_id = $1;",
                playlist_id,
            )

            # Add track
            result = await conn.fetchval(
                "INSERT INTO playlist_tracks (playlist_id, track_id, position) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING RETURNING id;",
                playlist_id,
                track_id,
                next_pos,
            )

            # Update playlist timestamp
            await conn.execute("UPDATE playlists SET updated_at = NOW() WHERE id = $1;", playlist_id)

            return {"added": result is not None, "error": None}

    async def remove_track_from_playlist(self, user_id: int, playlist_id: int, track_id: int) -> dict:
        """Remove track from playlist. Returns dict with 'removed' bool and optional 'error' string."""
        async with self.pool.acquire() as conn:
            # Verify playlist belongs to user
            playlist = await conn.fetchval(
                "SELECT id FROM playlists WHERE id = $1 AND user_id = $2;", playlist_id, user_id
            )
            if not playlist:
                return {"removed": False, "error": "playlist_not_found"}

            # Get position of track to remove
            position = await conn.fetchval(
                "SELECT position FROM playlist_tracks WHERE playlist_id = $1 AND track_id = $2;",
                playlist_id,
                track_id,
            )
            if position is None:
                return {"removed": False, "error": "track_not_found"}

            # Delete track
            await conn.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id = $1 AND track_id = $2;", playlist_id, track_id
            )

            # Reorder remaining tracks
            await conn.execute(
                "UPDATE playlist_tracks SET position = position - 1 WHERE playlist_id = $1 AND position > $2;",
                playlist_id,
                position,
            )

            # Update playlist timestamp
            await conn.execute("UPDATE playlists SET updated_at = NOW() WHERE id = $1;", playlist_id)

            return {"removed": True, "error": None}

    # ----------------------------------------------- #

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
