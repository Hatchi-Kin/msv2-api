from datetime import datetime
from typing import Optional

import asyncpg

from api.core.config import settings
from api.core.logger import logger
from api.models.auth import UserInDB
from api.repositories.database import DatabaseClient, validate_table_name


class AuthRepository:
    """Repository for user authentication and authorization operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.db = DatabaseClient(pool)
        validate_table_name(settings.AUTH_TABLE)
        self.table = settings.AUTH_TABLE

    async def create_user(
        self, email: str, username: Optional[str], hashed_password: str
    ) -> UserInDB:
        query = f"""
            INSERT INTO {self.table} (email, username, hashed_password)
            VALUES ($1, $2, $3)
            RETURNING id, email, username, hashed_password, is_active, 
                      is_admin, created_at, updated_at, jti, jti_expires_at;
        """
        row = await self.db.fetchrow(query, email, username, hashed_password)
        logger.info(f"User created: {email}")
        return UserInDB(**dict(row))

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        query = f"""
            SELECT id, email, username, hashed_password, is_active, is_admin, 
                   created_at, updated_at, jti, jti_expires_at 
            FROM {self.table} WHERE email = $1;
        """
        row = await self.db.fetchrow(query, email)
        return UserInDB(**dict(row)) if row else None

    async def update_user_jti(
        self, user_id: int, jti: str, jti_expires_at: datetime
    ) -> None:
        query = f"""
            UPDATE {self.table} 
            SET jti = $1, jti_expires_at = $2, updated_at = NOW() 
            WHERE id = $3;
        """
        await self.db.execute(query, jti, jti_expires_at, user_id)
        logger.debug(f"Updated JTI for user {user_id}")

    async def clear_user_jti(self, user_id: int) -> None:
        query = f"""
            UPDATE {self.table} 
            SET jti = NULL, jti_expires_at = NULL, updated_at = NOW() 
            WHERE id = $1;
        """
        await self.db.execute(query, user_id)
        logger.info(f"Cleared JTI for user {user_id}")

    async def get_all_users(self) -> list[UserInDB]:
        query = f"""
            SELECT id, email, username, hashed_password, is_active, is_admin, 
                   created_at, updated_at, jti, jti_expires_at 
            FROM {self.table};
        """
        rows = await self.db.fetch(query)
        return [UserInDB(**dict(row)) for row in rows]
