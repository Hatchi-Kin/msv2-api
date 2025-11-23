from typing import List

from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    path: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    shape: List[int]
