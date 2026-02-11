from fastapi import APIRouter

from api.core.dependencies import CurrentUser, LibraryRepo, InferenceRepo
from api.handlers.discovery import discovery_search_handler
from api.models.discovery import DiscoveryResponse

discovery_router = APIRouter(prefix="/discovery", tags=["Music Discovery"])


@discovery_router.get("/search", response_model=DiscoveryResponse)
async def discovery_search_endpoint(
    query: str,
    _user: CurrentUser,
    library_repo: LibraryRepo,
    inference_repo: InferenceRepo,
):
    """
    Search the library using natural language semantics.
    Returns tracks and the query vector for future refinement.
    """
    return await discovery_search_handler(query, library_repo, inference_repo)
