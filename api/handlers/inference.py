import asyncio

import httpx

from api.core.exceptions import APIException
from api.core.logger import logger
from api.models.inference import EmbeddingResponse
from api.repositories.inference import InferenceRepository


async def get_embeddings_handler(
    audio_minio_path: str,
    inference_repo: InferenceRepository,
    max_retries: int = 3,
) -> EmbeddingResponse:
    """
    Get embeddings for an audio file from inference service.
    Implements retry logic to handle Knative cold starts.

    Args:
        audio_minio_path: Path to audio file in MinIO bucket
        inference_repo: Inference repository instance
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        EmbeddingResponse with embeddings vector

    Raises:
        APIException: If inference service is unavailable (503)
    """
    logger.info(f"Requesting embeddings for: {audio_minio_path}")

    last_exception = None

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(
                    f"Retry attempt {attempt + 1}/{max_retries} for {audio_minio_path}"
                )

            result = await inference_repo.get_embeddings(audio_minio_path)
            logger.info(
                f"Successfully got embeddings for {audio_minio_path}: shape {result.shape}"
            )
            return result

        except httpx.TimeoutException as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Inference service timeout (attempt {attempt + 1}/{max_retries}). "
                    f"Retrying in {wait_time}s... This may be a cold start."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Inference service timeout after {max_retries} attempts")
                raise APIException(
                    detail=f"Inference service timeout after {max_retries} attempts. "
                    f"The service may be experiencing cold start issues.",
                    status_code=503,
                ) from e

        except httpx.HTTPStatusError as e:
            # HTTP error from inference service (4xx, 5xx)
            try:
                err_detail = e.response.json().get("detail", e.response.text)
            except Exception:
                err_detail = e.response.text

            logger.error(
                f"Inference service error {e.response.status_code}: {err_detail}"
            )
            raise APIException(
                detail=f"Inference service error: {err_detail}",
                status_code=503,
            ) from e

        except httpx.RequestError as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                logger.warning(
                    f"Failed to reach inference service (attempt {attempt + 1}/{max_retries}). "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"Failed to reach inference service after {max_retries} attempts"
                )
                raise APIException(
                    detail=f"Failed to reach inference service: {str(e)}",
                    status_code=503,
                ) from e

    # This should never be reached, but just in case
    raise APIException(
        detail=f"Failed to get embeddings after {max_retries} attempts",
        status_code=503,
    ) from last_exception


async def get_test(
    inference_repo: InferenceRepository,
):
    return await InferenceRepository.letstest(inference_repo)
