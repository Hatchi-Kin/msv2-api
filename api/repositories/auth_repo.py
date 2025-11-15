from datetime import datetime
from typing import Optional
import asyncpg
from api.models.auth import UserInDB


class AuthRepository:
    """Repository for user authentication and authorization operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_user(self, email: str, username: Optional[str], hashed_password: str) -> UserInDB:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, username, hashed_password)
                VALUES ($1, $2, $3)
                RETURNING id, email, username, hashed_password, is_active, 
                          is_admin, created_at, updated_at, jti, jti_expires_at;
                """,
                email,
                username,
                hashed_password,
            )
            return UserInDB(**dict(row))

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, username, hashed_password, is_active, is_admin, 
                       created_at, updated_at, jti, jti_expires_at 
                FROM users WHERE email = $1;
                """,
                email,
            )
            return UserInDB(**dict(row)) if row else None

    async def update_user_jti(self, user_id: int, jti: str, jti_expires_at: datetime) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users 
                SET jti = $1, jti_expires_at = $2, updated_at = NOW() 
                WHERE id = $3;
                """,
                jti,
                jti_expires_at,
                user_id,
            )

    async def clear_user_jti(self, user_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users 
                SET jti = NULL, jti_expires_at = NULL, updated_at = NOW() 
                WHERE id = $1;
                """,
                user_id,
            )

    async def get_all_users(self) -> list[UserInDB]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, email, username, hashed_password, is_active, is_admin, 
                       created_at, updated_at, jti, jti_expires_at 
                FROM users;
                """
            )
            return [UserInDB(**dict(row)) for row in rows]
