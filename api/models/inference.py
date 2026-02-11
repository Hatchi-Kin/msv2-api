from typing import List

from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    path: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    shape: List[int]


class TextEmbeddingRequest(BaseModel):
    text: str


class TextEmbeddingResponse(BaseModel):
    embedding: List[float]
