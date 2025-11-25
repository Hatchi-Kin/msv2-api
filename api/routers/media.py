from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from api.core.dependencies import CurrentUser, LibraryRepo, MediaRepo
from api.handlers.media import stream_audio_handler
from api.models.media import StreamRequest

media_router = APIRouter(prefix="/media", tags=["Audio Streaming"])


@media_router.post("/audio")
async def stream_audio_endpoint(
    request: Request,
    stream_request: StreamRequest,
    _user: CurrentUser,
    library_repo: LibraryRepo,
    media_repo: MediaRepo,
) -> StreamingResponse:
    """Stream audio from MinIO bucket. Example POST body: {"track_id": 155}"""
    return await stream_audio_handler(
        stream_request.track_id, request, library_repo, media_repo
    )
