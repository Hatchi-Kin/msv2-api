from api.core.exceptions import APIException, NotFoundException
from api.core.logger import logger
from api.models.coordinates import (
    ClusterInfo,
    CoordinatesStats,
    GenreDistribution,
    Point,
    PointsResponse,
    TrackNeighbors,
    VisualizationType,
)
from api.repositories.coordinates import CoordinatesRepository


async def get_all_points_handler(
    coords_repo: CoordinatesRepository,
    limit: int,
    offset: int,
    viz_type: VisualizationType = VisualizationType.DEFAULT,
) -> PointsResponse:
    """Get paginated coordinate points."""
    points_data = await coords_repo.get_all_points(limit, offset, viz_type)
    total = await coords_repo.count_points(viz_type)
    points = [Point(**point) for point in points_data]

    return PointsResponse(
        points=points,
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_statistics_handler(
    coords_repo: CoordinatesRepository,
    viz_type: VisualizationType = VisualizationType.DEFAULT,
) -> CoordinatesStats:
    """Get coordinate space statistics."""
    stats = await coords_repo.get_statistics(viz_type)

    # Calculate percentages for genre distribution
    total = stats["total_tracks"]
    top_genres = []
    for genre_data in stats["genre_distribution"]:
        percentage = (genre_data["count"] / total * 100) if total > 0 else 0
        top_genres.append(
            GenreDistribution(
                genre=genre_data["genre"],
                count=genre_data["count"],
                percentage=round(percentage, 2),
            )
        )

    return CoordinatesStats(
        total_tracks=stats["total_tracks"],
        total_clusters=stats["total_clusters"],
        top_genres=top_genres,
        largest_cluster=stats["largest_cluster"],
        largest_cluster_size=stats["largest_cluster_size"],
    )


async def search_tracks_handler(
    coords_repo: CoordinatesRepository,
    query: str,
    limit: int,
    viz_type: VisualizationType = VisualizationType.DEFAULT,
) -> list[Point]:
    """Search tracks in coordinate space."""
    if not query or len(query.strip()) < 2:
        raise APIException("Search query must be at least 2 characters")

    results = await coords_repo.search_tracks(query, limit, viz_type)
    return [Point(**point) for point in results]


async def get_cluster_handler(
    coords_repo: CoordinatesRepository,
    cluster_id: int,
    viz_type: VisualizationType = VisualizationType.DEFAULT,
) -> ClusterInfo:
    """Get all tracks in a specific cluster."""
    cluster_data = await coords_repo.get_cluster_tracks(cluster_id, viz_type)
    if not cluster_data:
        raise NotFoundException("Cluster", str(cluster_id))

    tracks = [Point(**track) for track in cluster_data["tracks"]]

    return ClusterInfo(
        cluster_id=cluster_data["cluster_id"],
        color=cluster_data["color"],
        track_count=cluster_data["track_count"],
        tracks=tracks,
    )


async def get_track_neighbors_handler(
    coords_repo: CoordinatesRepository,
    track_id: int,
    limit: int,
    viz_type: VisualizationType = VisualizationType.DEFAULT,
) -> TrackNeighbors:
    """Get nearest neighbors of a track in 3D space."""
    neighbors_data = await coords_repo.get_track_neighbors(track_id, limit, viz_type)
    if neighbors_data is None:
        raise NotFoundException("Track in coordinate space", str(track_id))

    neighbors = [Point(**point) for point in neighbors_data]
    logger.debug(f"Found {len(neighbors)} neighbors for track {track_id}")

    return TrackNeighbors(track_id=track_id, neighbors=neighbors)
