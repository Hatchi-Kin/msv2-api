from typing import List

from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    path: str


class EmbeddingResponse(BaseModel):
    embeddings: List[float]
    shape: List[int]
