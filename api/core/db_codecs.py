import ast
import asyncpg


def decode_vector(value: str) -> list[float] | None:
    """Decodes pgvector string '[1.2,3.4,...]' into a list."""
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


async def register_vector_codec(conn: asyncpg.Connection):
    """Register custom codec for 'vector' type with asyncpg."""
    await conn.set_type_codec(
        "vector",
        encoder=encode_vector,
        decoder=decode_vector,
        schema="public",
        format="text",
    )
