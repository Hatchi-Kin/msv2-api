from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from minio.error import S3Error

from api.repositories.music_db import MusicRepository
from api.repositories.music_storage import StorageRepository
from api.core.logger import logger


async def stream_audio_handler(
    track_id: int, request: Request, music_repo: MusicRepository, storage_repo: StorageRepository
):
    # Get track from database
    track = await music_repo.get_track_by_id(track_id, include_embeddings=False)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found in database")

    if not track.relative_path:
        raise HTTPException(status_code=400, detail="Track has no file path")

    try:
        # Get file size
        file_size = storage_repo.get_object_size_in_bytes(track.relative_path)

        # Check for Range header (for seeking/partial content)
        range_header = request.headers.get("range")

        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            range_match = range_header.replace("bytes=", "").split("-")
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            end = min(end, file_size - 1)
            content_length = end - start + 1

            # Get partial object
            response = storage_repo.get_object_stream(
                track.relative_path, offset=start, length=content_length
            )

            # Stream in 32KB chunks for efficient memory usage
            return StreamingResponse(
                response.stream(32 * 1024),
                status_code=206,
                media_type="audio/mpeg",
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(content_length),
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": f'inline; filename="{track.filename}"',
                },
            )
        else:
            # Full file request
            response = storage_repo.get_object_stream(track.relative_path)

            # Stream in 32KB chunks for efficient memory usage
            return StreamingResponse(
                response.stream(32 * 1024),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f'inline; filename="{track.filename}"',
                    "Content-Length": str(file_size),
                    "Accept-Ranges": "bytes",
                },
            )
    except S3Error as e:
        if e.code == "NoSuchKey":
            logger.error(f"Audio file not found in MinIO: {track.relative_path}")
            raise HTTPException(
                status_code=404, detail=f"Audio file not found in storage: {track.relative_path}"
            )
        logger.error(f"MinIO error while streaming track {track_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error streaming track {track_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error streaming audio: {str(e)}")
