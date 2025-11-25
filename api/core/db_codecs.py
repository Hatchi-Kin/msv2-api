import ast
import math

import asyncpg


def decode_vector(value: str | list | None) -> list[float] | None:
    """
    Decodes pgvector data into a list of floats.
    Handles strings '[1.2,3.4]', existing lists, or None.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return None


def encode_vector(value: list[float] | None) -> str | None:
    """Encodes a list of floats into pgvector string."""
    if value is None:
        return None
    return f"[{','.join(map(str, value))}]"


def normalize_vector(v: list[float]) -> list[float]:
    """
    Returns the normalized unit vector (length = 1).
    If the vector is zero-length, returns it as is (or could raise error).
    """
    if not v:
        return []
    norm = math.sqrt(sum(x * x for x in v))
    if norm == 0:
        return v
    return [x / norm for x in v]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Calculates cosine similarity between two vectors.
    Range: [-1, 1]. 1 = identical direction.
    """
    if not a or not b or len(a) != len(b):
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


async def register_vector_codec(conn: asyncpg.Connection):
    """Register custom codec for 'vector' type with asyncpg."""
    await conn.set_type_codec(
        "vector",
        encoder=encode_vector,
        decoder=decode_vector,
        schema="public",
        format="text",
    )
