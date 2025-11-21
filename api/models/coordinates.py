from typing import List, Optional

from pydantic import BaseModel

from enum import Enum

class VisualizationType(str, Enum):
    DEFAULT = "default"
    UMAP = "umap"

class Point(BaseModel):
    """Single point in 3D coordinate space with track metadata."""

    id: int
    x: float
    y: float
    z: float
    cluster: int
    cluster_color: str
    # Track metadata
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None


class PointsResponse(BaseModel):
    """Paginated response for coordinate points."""

    points: List[Point]
    total: int
    limit: int
    offset: int


class ClusterInfo(BaseModel):
    """Information about a specific cluster."""

    cluster_id: int
    color: str
    track_count: int
    tracks: List[Point]


class GenreDistribution(BaseModel):
    """Genre distribution statistics."""

    genre: str
    count: int
    percentage: float


class CoordinatesStats(BaseModel):
    """Overall coordinate space statistics."""

    total_tracks: int
    total_clusters: int
    top_genres: List[GenreDistribution]
    largest_cluster: Optional[int] = None
    largest_cluster_size: Optional[int] = None


class TrackNeighbors(BaseModel):
    """Nearest neighbors of a track in 3D space."""

    track_id: int
    neighbors: List[Point]
