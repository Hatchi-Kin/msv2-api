from api.core.exceptions import APIException
from api.core.logger import logger
from api.models.inference import EmbeddingResponse
from api.repositories.inference import InferenceRepository


async def get_embeddings_handler(
    audio_minio_path: str,
    inference_repo: InferenceRepository,
) -> EmbeddingResponse:
    """
    Get embeddings for an audio file from inference service.

    Args:
        audio_minio_path: Path to audio file in MinIO bucket
        inference_repo: Inference repository instance

    Returns:
        EmbeddingResponse with embeddings vector

    Raises:
        APIException: If inference service is unavailable (503)
    """
    logger.debug(f"Requesting embeddings for: {audio_minio_path}")
    
    try:
        result = await inference_repo.get_embeddings(audio_minio_path)
        logger.info(f"Got embeddings for {audio_minio_path}: shape {result.shape}")
        return result
    except RuntimeError as e:
        # Inference service is unavailable - return 503 instead of 500
        logger.error(f"Inference service unavailable: {e}")
        raise APIException(
            detail=f"Inference service unavailable: {str(e)}",
            status_code=503,
        )
