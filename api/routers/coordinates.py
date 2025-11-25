from fastapi import APIRouter, Query

from api.core.dependencies import (
    CoordinatesRepo,
    CurrentUser,
    Neighbors,
    PointsPagination,
    Search,
)
from api.handlers.coordinates import (
    get_all_points_handler,
    get_cluster_handler,
    get_statistics_handler,
    get_track_neighbors_handler,
    search_tracks_handler,
)
from api.models.coordinates import (
    ClusterInfo,
    CoordinatesStats,
    Point,
    PointsResponse,
    TrackNeighbors,
    VisualizationType,
)

coordinates_router = APIRouter(prefix="/library/coordinates", tags=["3D Coordinates"])


@coordinates_router.get("/points", response_model=PointsResponse)
async def get_coordinate_points(
    _user: CurrentUser,
    coords_repo: CoordinatesRepo,
    params: PointsPagination,
    viz_type: VisualizationType = Query(
        VisualizationType.DEFAULT, description="Visualization source table"
    ),
):
    """Get all coordinate points with track metadata."""
    return await get_all_points_handler(
        coords_repo, params.limit, params.offset, viz_type
    )


@coordinates_router.get("/stats", response_model=CoordinatesStats)
async def get_coordinate_stats(
    _user: CurrentUser,
    coords_repo: CoordinatesRepo,
    viz_type: VisualizationType = Query(
        VisualizationType.DEFAULT, description="Visualization source table"
    ),
):
    """Get overall coordinate space statistics."""
    return await get_statistics_handler(coords_repo, viz_type)


@coordinates_router.get("/search", response_model=list[Point])
async def search_coordinate_tracks(
    _user: CurrentUser,
    coords_repo: CoordinatesRepo,
    params: Search,
    viz_type: VisualizationType = Query(
        VisualizationType.DEFAULT, description="Visualization source table"
    ),
):
    """Search tracks by title, artist, album, or genre."""
    return await search_tracks_handler(coords_repo, params.q, params.limit, viz_type)


@coordinates_router.get("/cluster/{cluster_id}", response_model=ClusterInfo)
async def get_cluster_details(
    _user: CurrentUser,
    cluster_id: int,
    coords_repo: CoordinatesRepo,
    viz_type: VisualizationType = Query(
        VisualizationType.DEFAULT, description="Visualization source table"
    ),
):
    """Get all tracks in a specific cluster."""
    return await get_cluster_handler(coords_repo, cluster_id, viz_type)


@coordinates_router.get("/track/{track_id}/neighbors", response_model=TrackNeighbors)
async def get_track_neighbors(
    _user: CurrentUser,
    track_id: int,
    coords_repo: CoordinatesRepo,
    params: Neighbors,
    viz_type: VisualizationType = Query(
        VisualizationType.DEFAULT, description="Visualization source table"
    ),
):
    """Get nearest neighbors of a track in 3D space."""
    return await get_track_neighbors_handler(
        coords_repo, track_id, params.limit, viz_type
    )
