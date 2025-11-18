from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from api.core.dependencies import StorageRepo, MusicRepo, CurrentUser
from api.handlers.music_storage import stream_audio_handler
from api.models.music_storage import StreamRequest

music_storage_router = APIRouter(prefix="/stream", tags=["Audio Streaming"])


@music_storage_router.post("/audio")
async def stream_audio_endpoint(
    request: Request,
    stream_request: StreamRequest,
    _user: CurrentUser,
    music_repo: MusicRepo,
    storage_repo: StorageRepo,
) -> StreamingResponse:
    """Example POST body: {"track_id": 155}"""
    return await stream_audio_handler(stream_request.track_id, request, music_repo, storage_repo)
