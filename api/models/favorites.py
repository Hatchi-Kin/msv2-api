from pydantic import BaseModel


class FavoriteCheckResponse(BaseModel):
    """Response for checking if a track is favorited."""

    is_favorite: bool
