import httpx

from api.core.config import settings
from api.core.logger import logger
from api.models.inference import EmbeddingRequest, EmbeddingResponse


class InferenceRepository:
    """Repository for inference service operations."""

    def __init__(self, timeout: int = 600):
        self.timeout = timeout
        self.base_url = settings.MSV2_INFERENCE_URL

    @property
    def endpoint(self) -> str:
        """Get inference endpoint URL. Raises error if not configured."""
        if not self.base_url:
            raise RuntimeError(
                "MSV2_INFERENCE_URL is not configured. "
                "Set MSV2_INFERENCE_URL in your .env file or environment variables."
            )
        return f"{self.base_url.rstrip('/')}/inference/embeddings"

    @property
    def test(self):
        return f"{self.base_url.rstrip('/')}/test"

    async def get_embeddings(self, audio_minio_path: str) -> EmbeddingResponse:
        """
        Call inference service to get embeddings for audio file.

        Args:
            audio_minio_path: Path to audio file in MinIO bucket

        Returns:
            EmbeddingResponse with embeddings vector

        Raises:
            RuntimeError: If inference service is unavailable or returns error
        """
        payload = EmbeddingRequest(path=audio_minio_path)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Calling inference service for: {audio_minio_path}")
                response = await client.post(
                    self.endpoint,
                    content=payload.model_dump_json(),
                    headers={"Content-Type": "application/json"},
                )

                if not response.is_success:
                    # Extract error detail from service response
                    try:
                        err_detail = response.json().get("detail", response.text)
                    except Exception:
                        err_detail = response.text
                    logger.error(f"Inference service error {response.status_code}: {err_detail}")
                    raise RuntimeError(
                        f"Inference service returned {response.status_code}: {err_detail}"
                    )

                result = EmbeddingResponse(**response.json())
                logger.debug(f"Got embeddings for {audio_minio_path}: shape {result.shape}")
                return result

        except httpx.TimeoutException as e:
            logger.error(f"Inference service timeout: {e}")
            raise RuntimeError(f"Inference service timeout after {self.timeout}s") from e
        except httpx.RequestError as e:
            logger.error(f"Failed to reach inference service: {e}")
            raise RuntimeError(f"Failed to reach inference service: {e}") from e


    async def letstest(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.test,
                headers={"Content-Type": "application/json"},
            )
            return response
