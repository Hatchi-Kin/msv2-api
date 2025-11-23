from fastapi import APIRouter

from api.core.dependencies import CurrentUser, InferenceRepo
from api.handlers.inference import get_embeddings_handler
from api.models.inference import EmbeddingRequest, EmbeddingResponse

inference_router = APIRouter(prefix="/inference", tags=["Inference"])


@inference_router.post("/embeddings", response_model=EmbeddingResponse)
async def get_embeddings_endpoint(
    request: EmbeddingRequest,
    _user: CurrentUser,
    inference_repo: InferenceRepo,
) -> EmbeddingResponse:
    """Get embeddings for an audio file from inference service."""
    return await get_embeddings_handler(request.path, inference_repo)
