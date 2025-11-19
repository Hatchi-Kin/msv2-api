from api.core.config import settings
from api.core.exceptions import MaxLimitException, NotFoundException
from api.models.metadata import FavoritesList
from api.models.responses import OperationResult
from api.repositories.favorites import FavoritesRepository


async def add_favorite_handler(
    user_id: int, track_id: int, favorites_repo: FavoritesRepository
) -> OperationResult:
    # Check if track exists
    if not await favorites_repo.track_exists(track_id):
        raise NotFoundException("Track", str(track_id))

    # Check limit
    count = await favorites_repo.get_favorites_count(user_id)
    if count >= settings.MAX_FAVORITES_PER_USER:
        raise MaxLimitException("favorites", settings.MAX_FAVORITES_PER_USER)

    # Add favorite
    added = await favorites_repo.add_favorite(user_id, track_id)
    message = "Track added to favorites" if added else "Track already in favorites"
    return OperationResult(success=added, message=message)


async def remove_favorite_handler(
    user_id: int, track_id: int, favorites_repo: FavoritesRepository
) -> OperationResult:
    removed = await favorites_repo.remove_favorite(user_id, track_id)
    if not removed:
        raise NotFoundException("Favorite", str(track_id))
    return OperationResult(success=True, message="Track removed from favorites")


async def get_favorites_handler(user_id: int, favorites_repo: FavoritesRepository) -> FavoritesList:
    tracks, total = await favorites_repo.get_user_favorites(user_id)
    return FavoritesList(tracks=tracks, total=total)


async def check_favorite_handler(
    user_id: int, track_id: int, favorites_repo: FavoritesRepository
) -> dict:
    """Check if a track is in user's favorites."""
    is_favorite = await favorites_repo.is_favorite(user_id, track_id)
    return {"is_favorite": is_favorite}
