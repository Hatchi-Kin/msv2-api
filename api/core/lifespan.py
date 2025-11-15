import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.core.config import settings
from api.core.db_codecs import register_vector_codec


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    pool = await asyncpg.create_pool(settings.DATABASE_URL, init=register_vector_codec)
    if pool is None:
        raise Exception("Could not connect to the database")

    app.state.db_pool = pool
    print("Asyncpg Pool Connected (with vector codec)")

    yield

    # Shutdown
    await app.state.db_pool.close()
    print("Asyncpg Pool Disconnected")
