from fastapi import Request
from fastapi.responses import StreamingResponse
from minio.error import S3Error

from api.core.config import settings
from api.core.exceptions import APIException, NotFoundException
from api.core.logger import logger
from api.repositories.metadata import MetadataRepository
from api.repositories.objects import ObjectsRepository


async def stream_audio_handler(
    track_id: int,
    request: Request,
    metadata_repo: MetadataRepository,
    objects_repo: ObjectsRepository,
):
    # Get track from database
    track = await metadata_repo.get_track_by_id(track_id, include_embeddings=False)
    if not track:
        raise NotFoundException("Track", str(track_id))

    if not track.relative_path:
        raise APIException("Track has no file path")

    try:
        # Get file size
        file_size = objects_repo.get_object_size_in_bytes(track.relative_path)

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
            response = objects_repo.get_object_stream(
                track.relative_path, offset=start, length=content_length
            )

            logger.debug(f"Streaming track {track_id} (range: {start}-{end})")
            return StreamingResponse(
                response.stream(settings.AUDIO_STREAM_CHUNK_SIZE),
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
            response = objects_repo.get_object_stream(track.relative_path)

            logger.debug(f"Streaming full track {track_id}")
            return StreamingResponse(
                response.stream(settings.AUDIO_STREAM_CHUNK_SIZE),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f'inline; filename="{track.filename}"',
                    "Content-Length": str(file_size),
                    "Accept-Ranges": "bytes",
                },
            )
    except S3Error as e:
        if e.code == "NoSuchKey":
            logger.error(f"Audio file not found in storage: {track.relative_path}")
            raise NotFoundException("Audio file", track.relative_path)
        elif e.code in ["ServiceUnavailable", "SlowDown", "InternalError"]:
            logger.error(f"MinIO service unavailable: {e}")
            raise APIException("Storage service temporarily unavailable", status_code=503)
        else:
            logger.error(f"MinIO error while streaming track {track_id}: {str(e)}")
            raise APIException(f"Storage error: {str(e)}", status_code=500)
    except Exception as e:
        logger.error(f"Unexpected error streaming track {track_id}: {str(e)}")
        raise APIException(f"Error streaming audio: {str(e)}", status_code=500)
