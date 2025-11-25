import httpx

from api.core.config import settings
from api.core.logger import logger
from api.models.inference import EmbeddingRequest, EmbeddingResponse


class InferenceRepository:
    """Repository for inference service HTTP operations."""

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
            httpx.TimeoutException: If request times out
            httpx.RequestError: If request fails
            httpx.HTTPStatusError: If response has error status code
        """
        payload = EmbeddingRequest(path=audio_minio_path)

        logger.debug(f"Calling inference service for: {audio_minio_path}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.endpoint,
                content=payload.model_dump_json(),
                headers={"Content-Type": "application/json"},
            )

            # Raise exception for error status codes
            response.raise_for_status()

            result = EmbeddingResponse(**response.json())
            logger.debug(f"Received embeddings: shape {result.shape}")
            return result

    async def letstest(self):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self.test,
                headers={"Content-Type": "application/json"},
            )
            return {
                "status_code": response.status_code,
                "content": response.text,
                "inference_url": self.test,
            }
