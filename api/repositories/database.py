from typing import Any, Optional

import asyncpg

from api.core.logger import logger


def validate_table_name(table_name: str) -> None:
    """Validate table name contains only safe characters to prevent SQL injection."""
    if not table_name.replace("_", "").isalnum():
        raise ValueError(f"Invalid table name: {table_name}")


class DatabaseClient:
    """Database client with common operations and error handling."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Execute query and return single row."""
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetchrow(query, *args)
            except Exception as e:
                logger.error(f"Database error in fetchrow: {e}")
                raise

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        """Execute query and return all rows."""
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetch(query, *args)
            except Exception as e:
                logger.error(f"Database error in fetch: {e}")
                raise

    async def fetchval(self, query: str, *args) -> Any:
        """Execute query and return single value."""
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetchval(query, *args)
            except Exception as e:
                logger.error(f"Database error in fetchval: {e}")
                raise

    async def execute(self, query: str, *args) -> str:
        """Execute query without returning results."""
        async with self.pool.acquire() as conn:
            try:
                return await conn.execute(query, *args)
            except Exception as e:
                logger.error(f"Database error in execute: {e}")
                raise
