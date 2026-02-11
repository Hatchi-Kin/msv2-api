import httpx

from api.core.config import settings
from api.core.logger import logger
from api.models.inference import (
    EmbeddingRequest,
    EmbeddingResponse,
    TextEmbeddingRequest,
    TextEmbeddingResponse,
)


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

    @property
    def clap_endpoint(self) -> str:
        """Get CLAP inference endpoint URL."""
        url = settings.CLAP_INFERENCE_URL or self.base_url
        if not url:
            raise RuntimeError("CLAP_INFERENCE_URL is not configured.")
        return f"{url.rstrip('/')}/embed"

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

    async def get_text_embedding(self, text: str) -> TextEmbeddingResponse:
        """Call CLAP inference service to get embedding for text."""
        payload = TextEmbeddingRequest(text=text)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.clap_endpoint,
                content=payload.model_dump_json(),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return TextEmbeddingResponse(**response.json())
