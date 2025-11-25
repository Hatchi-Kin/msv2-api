from pydantic import BaseModel, Field

from api.core.config import settings


class PaginationParams(BaseModel):
    """Pagination parameters with validation."""

    limit: int = Field(
        default=settings.DEFAULT_ARTIST_LIMIT,
        ge=1,
        le=settings.MAX_ARTIST_LIMIT,
        description=f"Number of items to return (max {settings.MAX_ARTIST_LIMIT})",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PointsPaginationParams(BaseModel):
    """Pagination for coordinate points."""

    limit: int = Field(
        default=settings.DEFAULT_POINTS_LIMIT,
        ge=1,
        le=settings.MAX_POINTS_LIMIT,
        description=f"Number of points to return (max {settings.MAX_POINTS_LIMIT})",
    )
    offset: int = Field(default=0, ge=0, description="Number of points to skip")


class SearchParams(BaseModel):
    """Search query parameters with validation."""

    q: str = Field(
        min_length=2, max_length=100, description="Search query (min 2 characters)"
    )
    limit: int = Field(
        default=settings.DEFAULT_SEARCH_LIMIT,
        ge=1,
        le=settings.MAX_SEARCH_LIMIT,
        description=f"Number of results to return (max {settings.MAX_SEARCH_LIMIT})",
    )


class NeighborsParams(BaseModel):
    """Parameters for nearest neighbors query."""

    limit: int = Field(
        default=settings.DEFAULT_NEIGHBORS_LIMIT,
        ge=1,
        le=settings.MAX_NEIGHBORS_LIMIT,
        description=f"Number of neighbors to return (max {settings.MAX_NEIGHBORS_LIMIT})",
    )
