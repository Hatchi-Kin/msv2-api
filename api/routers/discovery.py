from fastapi import APIRouter

from api.core.dependencies import CurrentUser, LibraryRepo, InferenceRepo, DiscoveryRepo
from api.handlers.discovery import discovery_search_handler, discovery_refine_handler
from api.models.discovery import DiscoveryResponse, DiscoveryRefineRequest

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


@discovery_router.post("/refine", response_model=DiscoveryResponse)
async def discovery_refine_endpoint(
    request: DiscoveryRefineRequest,
    _user: CurrentUser,
    library_repo: LibraryRepo,
    discovery_repo: DiscoveryRepo,
):
    """
    Refine existing search results using latent space steering.
    Allows sliding toward/away from specific anchors (Acoustic, Energy, etc.).
    """
    return await discovery_refine_handler(request, library_repo, discovery_repo)
