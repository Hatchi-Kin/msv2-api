from typing import Optional

import asyncpg

from api.core.config import settings
from api.core.db_codecs import decode_vector, normalize_vector
from api.core.logger import logger
from api.models.library import Track, TrackList
from api.repositories.database import DatabaseClient, validate_table_name


class LibraryRepository:
    """Repository for lirary / megaset db operations."""

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

    async def get_random_track(
        self, include_embeddings: bool = False
    ) -> Optional[Track]:
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
        query = (
            f"SELECT DISTINCT album_folder FROM {self.table} WHERE artist_folder = $1;"
        )
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

    async def get_similar_tracks(
        self, track_id: int, limit: int
    ) -> list[tuple[Track, float]]:
        """
        Get similar tracks using pgvector cosine distance.
        Optimized to use HNSW index for 16k+ song library.

        Args:
            track_id: ID of the track to find similar tracks for
            limit: Number of similar tracks to return

        Returns:
            List of tuples: (track, distance_score)
        """
        # Optimized query: Use subquery instead of CTE to allow HNSW index usage
        query = f"""
            SELECT 
                id, filename, filepath, relative_path, album_folder, 
                artist_folder, filesize, title, artist, album, 
                year, tracknumber, genre, top_5_genres, created_at,
                (embedding_512_vector <=> (
                    SELECT embedding_512_vector 
                    FROM {self.table} 
                    WHERE id = $1
                )) as distance
            FROM {self.table}
            WHERE id != $1 
                AND embedding_512_vector IS NOT NULL
            ORDER BY embedding_512_vector <=> (
                SELECT embedding_512_vector 
                FROM {self.table} 
                WHERE id = $1
            )
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

    async def get_playlist_centroid(self, playlist_id: int) -> Optional[list[float]]:
        """
        Calculate the centroid (average vector) of a playlist.
        """
        query = f"""
            SELECT AVG(embedding_512_vector) as centroid
            FROM {self.table} t
            JOIN playlist_tracks pt ON t.id = pt.track_id
            WHERE pt.playlist_id = $1 AND t.embedding_512_vector IS NOT NULL;
        """
        # Note: pgvector supports AVG() on vectors directly
        centroid = await self.db.fetchval(query, playlist_id)

        # Robustly decode the vector (handle string/list/None)
        centroid_vector = decode_vector(centroid)

        if not centroid_vector:
            return None

        # NORMALIZE the centroid.
        # Even if DB vectors are raw (unnormalized), we normalize the query vector (centroid).
        # For Cosine Distance (<=>), the magnitude of the query vector doesn't affect the ranking,
        # only the angle matters. Normalizing ensures a standard unit length for numerical stability
        # and compatibility if we ever switch to Dot Product.
        return normalize_vector(centroid_vector)

    async def get_playlist_sample(
        self, playlist_id: int, max_tracks: int = 10
    ) -> list[dict]:
        """
        Get a sample of tracks from a playlist for analysis.

        For small playlists (<=max_tracks), returns all tracks.
        For larger playlists, uses stratified sampling (beginning, middle, end).
        """
        # First, get total count
        count_query = """
            SELECT COUNT(*) 
            FROM playlist_tracks 
            WHERE playlist_id = $1;
        """
        total = await self.db.fetchval(count_query, playlist_id)

        if total <= max_tracks:
            # Small playlist - get all tracks
            query = f"""
                SELECT t.id, t.title, t.artist, t.album, t.genre, t.top_5_genres,
                       t.year, t.tracknumber
                FROM {self.table} t
                JOIN playlist_tracks pt ON t.id = pt.track_id
                WHERE pt.playlist_id = $1
                ORDER BY pt.position;
            """
            rows = await self.db.fetch(query, playlist_id)
        else:
            # Large playlist - stratified sampling
            # Sample evenly across the playlist (beginning, middle, end)
            step = total / max_tracks
            positions = [int(i * step) for i in range(max_tracks)]

            query = f"""
                SELECT t.id, t.title, t.artist, t.album, t.genre, t.top_5_genres,
                       t.year, t.tracknumber
                FROM {self.table} t
                JOIN playlist_tracks pt ON t.id = pt.track_id
                WHERE pt.playlist_id = $1 AND pt.position = ANY($2::int[])
                ORDER BY pt.position;
            """
            rows = await self.db.fetch(query, playlist_id, positions)

        return [dict(row) for row in rows]

    async def search_hidden_gems(
        self,
        centroid: list[float],
        exclude_ids: list[int],
        exclude_artists: list[str] = None,
        limit: int = 5,
    ) -> list[tuple[Track, float]]:
        """
        Find tracks similar to the centroid but NOT in the exclusion list.
        Hybrid Search: Vector Distance + Exclusion Filter.
        Optimized to use HNSW index for 16k+ song library.
        """
        if not centroid:
            return []

        # Format exclusion list for SQL (empty arrays work fine with cardinality check)
        if not exclude_ids:
            exclude_ids = []
        if not exclude_artists:
            exclude_artists = []

        # Optimized query: Don't select embedding, use ORDER BY with vector operator
        query = f"""
            SELECT 
                id, filename, filepath, relative_path, album_folder, artist_folder, 
                filesize, title, artist, album, year, tracknumber, genre, 
                top_5_genres, created_at,
                (embedding_512_vector <=> $1) as distance
            FROM {self.table}
            WHERE embedding_512_vector IS NOT NULL
                AND (cardinality($2::int[]) = 0 OR id != ALL($2::int[]))
                AND (cardinality($3::text[]) = 0 OR artist != ALL($3::text[]))
            ORDER BY embedding_512_vector <=> $1
            LIMIT $4;
        """

        rows = await self.db.fetch(query, centroid, exclude_ids, exclude_artists, limit)

        results = []
        for row in rows:
            row_dict = dict(row)
            distance = row_dict.pop("distance")
            track = Track(**row_dict)
            results.append((track, float(distance)))

        logger.debug(
            f"Found {len(results)} hidden gems (excluded {len(exclude_artists)} artists)"
        )
        return results

    async def update_track_metadata(self, track_id: int, updates: dict) -> bool:
        """
        Update specific fields of a track.
        """
        if not updates:
            return False

        # Construct dynamic update query
        set_clauses = []
        values = [track_id]
        for i, (key, value) in enumerate(updates.items(), start=2):
            # Validate key against allowed columns to prevent injection
            if key not in [
                "genre",
                "top_5_genres",
                "bpm",
                "key",
                "energy",
                "danceability",
                "valence",
            ]:
                logger.warning(f"Attempted to update invalid column: {key}")
                continue
            set_clauses.append(f"{key} = ${i}")
            values.append(value)

        if not set_clauses:
            return False

        query = f"""
            UPDATE {self.table}
            SET {", ".join(set_clauses)}
            WHERE id = $1;
        """
        await self.db.execute(query, *values)
        return True

    async def search_hidden_gems_with_filters(
        self,
        centroid: list[float],
        exclude_ids: list[int],
        exclude_artists: list[str],
        min_bpm: float = 0,
        max_bpm: float = 999,
        min_energy: float = 0,
        max_energy: float = 1.0,
        limit: int = 10,
    ) -> list[Track]:
        """
        Search for tracks similar to the centroid, applying filters.
        Optimized for pgvector HNSW index with 16k+ songs.
        """

        # Optimized query:
        # 1. Don't SELECT embedding_512_vector (saves ~2KB per row of network transfer)
        # 2. Use ORDER BY before WHERE filters for better HNSW index usage
        # 3. Apply filters as post-processing to leverage vector index first
        query = f"""
            SELECT 
                id, filename, filepath, relative_path, album_folder, artist_folder, 
                filesize, title, artist, album, year, tracknumber, genre, 
                top_5_genres, created_at, bpm, energy, brightness, harmonic_ratio, 
                estimated_key,
                (embedding_512_vector <=> $1) as distance
            FROM {self.table}
            WHERE 
                embedding_512_vector IS NOT NULL
                AND bpm >= $4 AND bpm <= $5
                AND energy >= $6 AND energy <= $7
                AND (cardinality($2::int[]) = 0 OR id != ALL($2::int[]))
                AND (cardinality($3::text[]) = 0 OR artist != ALL($3::text[]))
            ORDER BY embedding_512_vector <=> $1
            LIMIT $8;
        """

        rows = await self.db.fetch(
            query,
            centroid,
            exclude_ids or [],
            exclude_artists or [],
            min_bpm,
            max_bpm,
            min_energy,
            max_energy,
            limit,
        )

        # Build Track objects without embedding (we don't need it for results)
        tracks = []
        for row in rows:
            track_dict = dict(row)
            # Remove distance field, keep it as Track attribute if needed
            track_dict.pop("distance", None)
            # No need to decode embedding since we didn't select it
            tracks.append(Track(**track_dict))

        return tracks
