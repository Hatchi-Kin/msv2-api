import asyncpg
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from minio import Minio

from api.core.config import settings
from api.core.dependencies import get_db_pool, get_minio_client
from api.core.logger import logger

health_router = APIRouter(tags=["health"], include_in_schema=False)


@health_router.get("/")
def root_endpoint():
    """Root endpoint for quick API check."""
    return {"message": "Welcome to the MSV2 Webapp API!"}


@health_router.get("/health")
async def get_health_check_endpoint(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    minio_client: Minio = Depends(get_minio_client),
):
    """
    Health check for k3s liveness/readiness probes.
    Returns 200 if healthy, 503 if any dependency is down.
    """
    health = {"status": "healthy", "database": "unknown", "storage": "unknown"}

    # Check database connection
    try:
        async with db_pool.acquire(timeout=2) as conn:
            await conn.fetchval("SELECT 1")
        health["database"] = "healthy"
    except Exception as e:
        health["database"] = "unhealthy"
        health["status"] = "degraded"
        logger.error(f"Database health check failed: {e}")

    # Check MinIO connection
    try:
        minio_client.bucket_exists(settings.MINIO_BUCKET)
        health["storage"] = "healthy"
    except Exception as e:
        health["storage"] = "unhealthy"
        health["status"] = "degraded"
        logger.error(f"MinIO health check failed: {e}")

    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)


@health_router.get("/favicon.ico")
async def get_favicon_endpoint():
    """Return 204 No Content for favicon requests to avoid errors."""
    from fastapi.responses import Response

    return Response(status_code=204)
