import ast
from datetime import datetime
from typing import Optional, Dict, Any

import asyncpg

from api.core.config import settings
from api.models.music import MegasetTrack, TrackList
from api.models.auth import UserInDB


class PostgresConnector:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(settings.DATABASE_URL)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    # ----------------------------------------------- #

    async def create_user(
        self, email: str, username: Optional[str], hashed_password: str
    ) -> UserInDB:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, username, hashed_password)
                VALUES ($1, $2, $3)
                RETURNING id, email, username, hashed_password, is_active, is_admin, created_at, updated_at, jti, jti_expires_at;
                """,
                email,
                username,
                hashed_password,
            )
            return UserInDB(**dict(row))

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, username, hashed_password, is_active, is_admin, created_at, updated_at, jti, jti_expires_at FROM users WHERE email = $1;",
                email,
            )
            if row:
                # Explicitly map fields to UserInDB to ensure correct data handling
                return UserInDB(
                    id=row["id"],
                    email=row["email"],
                    username=row["username"],
                    hashed_password=row["hashed_password"],
                    is_active=row["is_active"],
                    is_admin=row["is_admin"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    jti=row["jti"],
                    jti_expires_at=row["jti_expires_at"],
                )
            return None

    async def update_user_jti(
        self, user_id: int, jti: str, jti_expires_at: datetime
    ) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET jti = $1, jti_expires_at = $2, updated_at = NOW() WHERE id = $3;",
                jti,
                jti_expires_at,
                user_id,
            )

    async def get_user_by_jti(self, jti: str) -> Optional[UserInDB]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, username, hashed_password, is_active, is_admin, created_at, updated_at, jti, jti_expires_at FROM users WHERE jti = $1;",
                jti,
            )
            if row:
                return UserInDB(**dict(row))
            return None

    async def clear_user_jti(self, user_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET jti = NULL, jti_expires_at = NULL, updated_at = NOW() WHERE id = $1;",
                user_id,
            )

    # ----------------------------------------------- #

    async def count_songs(self) -> int:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM megaset;")
            return result

    async def get_random_song(
        self, include_embeddings: bool = False
    ) -> Optional[MegasetTrack]:
        async with self.pool.acquire() as conn:
            columns = "*"
            if not include_embeddings:
                columns = "id, filename, filepath, relative_path, album_folder, artist_folder, filesize, title, artist, album, year, tracknumber, genre, top_5_genres, created_at"

            query = f"SELECT {columns} FROM megaset ORDER BY RANDOM() LIMIT 1;"
            row = await conn.fetchrow(query)
            if row:
                # Convert asyncpg.Record to dict, then to MegasetTrack
                song_data = dict(row)
                # asyncpg returns datetime objects, pydantic handles them
                # vector type from pgvector is returned as a string '[f1,f2,...]'
                # Convert embedding_512_vector from string to list of floats
                if song_data.get("embedding_512_vector"):
                    embedding_val = song_data["embedding_512_vector"]
                    if isinstance(embedding_val, str):
                        # The vector is stored as a string like '[1.2, 3.4, ...]'
                        song_data["embedding_512_vector"] = ast.literal_eval(
                            embedding_val
                        )
                return MegasetTrack(**song_data)
            return None

    async def get_song_by_id(
        self, song_id: int, include_embeddings: bool = False
    ) -> Optional[MegasetTrack]:
        async with self.pool.acquire() as conn:
            columns = "*"
            if not include_embeddings:
                columns = "id, filename, filepath, relative_path, album_folder, artist_folder, filesize, title, artist, album, year, tracknumber, genre, top_5_genres, created_at"

            query = f"SELECT {columns} FROM megaset WHERE id = $1;"
            row = await conn.fetchrow(query, song_id)
            if row:
                song_data = dict(row)
                if song_data.get("embedding_512_vector"):
                    embedding_val = song_data["embedding_512_vector"]
                    if isinstance(embedding_val, str):
                        song_data["embedding_512_vector"] = ast.literal_eval(
                            embedding_val
                        )
                return MegasetTrack(**song_data)
            return None

    async def get_artist_list(self) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT artist_folder FROM megaset;")
            artists = [row["artist_folder"] for row in rows if row["artist_folder"]]
            return {"artists": artists}

    async def get_album_list_from_artist(self, artist_name: str) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT album_folder FROM megaset WHERE artist_folder = $1;",
                artist_name,
            )
            albums = [row["album_folder"] for row in rows if row["album_folder"]]
            return {"albums": albums}

    async def get_tracklist_from_album(
        self, album_name: str, include_embeddings: bool = False
    ) -> TrackList:

        columns = "*"
        if not include_embeddings:
            columns = "id, filename, filepath, relative_path, album_folder, artist_folder, filesize, title, artist, album, year, tracknumber, genre, top_5_genres, created_at"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT {columns} FROM megaset WHERE album_folder = $1;",
                album_name,
            )
            tracks = []
            for row in rows:
                track_data = dict(row)
                if track_data.get("embedding_512_vector"):
                    embedding_val = track_data["embedding_512_vector"]
                    if isinstance(embedding_val, str):
                        track_data["embedding_512_vector"] = ast.literal_eval(
                            embedding_val
                        )
                tracks.append(MegasetTrack(**track_data))
            return TrackList(tracks=tracks)

    async def get_tracklist_from_artist_and_album(
        self, artist_name: str, album_name: str, include_embeddings: bool = False
    ) -> TrackList:

        columns = "*"
        if not include_embeddings:
            columns = "id, filename, filepath, relative_path, album_folder, artist_folder, filesize, title, artist, album, year, tracknumber, genre, top_5_genres, created_at"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT {columns} FROM megaset WHERE artist_folder = $1 AND album = $2;",
                artist_name,
                album_name,
            )
            tracks = []
            for row in rows:
                track_data = dict(row)
                if track_data.get("embedding_512_vector"):
                    embedding_val = track_data["embedding_512_vector"]
                    if isinstance(embedding_val, str):
                        track_data["embedding_512_vector"] = ast.literal_eval(
                            embedding_val
                        )
                tracks.append(MegasetTrack(**track_data))
            return TrackList(tracks=tracks)

    async def get_all_users(self) -> list[UserInDB]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, email, username, hashed_password, is_active, is_admin, created_at, updated_at, jti, jti_expires_at FROM users;"
            )
            return [UserInDB(**dict(row)) for row in rows]
