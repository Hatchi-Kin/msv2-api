from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from api.core.dependencies import ObjectsRepo, CurrentUser, MetadataRepo
from api.handlers.objects import stream_audio_handler
from api.models.objects import StreamRequest

objects_router = APIRouter(prefix="/stream", tags=["Audio Streaming"])


@objects_router.post("/audio")
async def stream_audio_endpoint(
    request: Request,
    stream_request: StreamRequest,
    _user: CurrentUser,
    metadata_repo: MetadataRepo,
    objects_repo: ObjectsRepo,
) -> StreamingResponse:
    """Stream audio from MinIO bucket. Example POST body: {"track_id": 155}"""
    return await stream_audio_handler(stream_request.track_id, request, metadata_repo, objects_repo)
