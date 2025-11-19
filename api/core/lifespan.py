from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from minio import Minio

from api.core.config import settings
from api.core.db_codecs import register_vector_codec
from api.core.logger import logger


async def startup_database_pool(app: FastAPI):
    """Initialize database connection pool with timeouts and limits."""
    pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        init=register_vector_codec,
        min_size=5,  # Minimum connections to maintain
        max_size=20,  # Maximum connections allowed
        command_timeout=30,  # Query timeout in seconds
        timeout=5,  # Connection acquisition timeout in seconds
    )
    if pool is None:
        raise Exception("Could not connect to the database")

    app.state.db_pool = pool
    logger.info("Asyncpg Pool Connected (with vector codec, min=5, max=20)")


def startup_minio_client(app: FastAPI):
    """Initialize MinIO client and verify connection."""
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )

    # Verify connection by checking if bucket exists
    try:
        if minio_client.bucket_exists(settings.MINIO_BUCKET):
            logger.info(
                f"MinIO Client Connected to {settings.MINIO_ENDPOINT} (bucket: {settings.MINIO_BUCKET})"
            )
        else:
            logger.warning(f"MinIO bucket '{settings.MINIO_BUCKET}' does not exist!")
    except Exception as e:
        logger.warning(f"Could not verify MinIO connection: {e}")

    app.state.minio_client = minio_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_database_pool(app)
    startup_minio_client(app)

    yield

    # Shutdown
    await app.state.db_pool.close()
    logger.info("Asyncpg Pool Disconnected")
    # Database pool = persistent connections → must close
    # MinIO client = on-demand HTTP requests → auto-cleanup
