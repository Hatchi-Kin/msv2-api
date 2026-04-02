"""
Router for downloading files from MinIO.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from minio import Minio
from minio.error import S3Error

from api.core.config import settings

downloads_router = APIRouter(prefix="/downloads", tags=["downloads"])


def get_minio_client() -> Minio:
    """Get configured MinIO client."""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


@downloads_router.get("/database")
async def download_database(
    path: str = Query(..., description="Path to file in MinIO, e.g. 'databases/CoSing_enriched_v2.db'"),
    bucket: str = Query("mars-db", description="MinIO bucket name"),
):
    """
    Download a database file from MinIO.
    
    Example: GET /downloads/database?path=databases/CoSing_enriched_v2.db&bucket=mars-db
    
    Returns the file as a streaming download.
    """
    
    client = get_minio_client()
    
    try:
        # Check if file exists and get metadata
        stat = client.stat_object(bucket, path)
        
        # Stream the file
        response = client.get_object(bucket, path)
        
        # Extract filename from path
        filename = path.split("/")[-1]
        
        return StreamingResponse(
            response.stream(32*1024),  # 32KB chunks
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(stat.size),
                "X-File-Size-GB": f"{stat.size / (1024**3):.2f}",
            }
        )
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
