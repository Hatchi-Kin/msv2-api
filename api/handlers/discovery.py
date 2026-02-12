from typing import List, Tuple

import numpy as np

from api.core.config import settings
from api.core.exceptions import NotFoundException
from api.models.discovery import (
    DiscoveryResponse,
    ScoredTrack,
    ScoredTrackList,
    DiscoveryRefineRequest,
)
from api.repositories.inference import InferenceRepository
from api.repositories.library import LibraryRepository
from api.repositories.discovery import DiscoveryRepository
from api.models.library import Track


def _filter_diverse_results(
    candidates: List[Tuple[Track, float]], limit: int
) -> List[ScoredTrack]:
    """Helper to apply artist diversity filtering (Max 1 track per artist_folder)."""
    seen_artists = set()
    filtered_results = []

    for track, distance in candidates:
        if track.artist_folder not in seen_artists:
            filtered_results.append(ScoredTrack(track=track, similarity_score=distance))
            seen_artists.add(track.artist_folder)

        if len(filtered_results) >= limit:
            break

    return filtered_results


async def discovery_search_handler(
    query: str,
    library_repo: LibraryRepository,
    inference_repo: InferenceRepository,
) -> DiscoveryResponse:
    """
    Handle natural language discovery search.
    1. Text -> Embedding
    2. Vector Search (Candidates)
    3. Python-side Artist Diversity Filtering
    """
    # 1. Get Text Embedding
    embedding_resp = await inference_repo.get_text_embedding(query)

    # 2. Get Candidates (Top 40)
    candidates = await library_repo.search_semantic_by_vector(
        embedding_resp.embedding, limit=settings.SIMILAR_TRACKS_LIMIT
    )

    if not candidates:
        raise NotFoundException("Discovery matches", query)

    # 3. Apply Diversity Filter
    results = _filter_diverse_results(candidates, settings.SIMILAR_TRACKS_RETURNED)

    # 4. Wrap and Return
    return DiscoveryResponse(
        results=ScoredTrackList(tracks=results),
        query_vector=embedding_resp.embedding,
    )


async def discovery_refine_handler(
    request: DiscoveryRefineRequest,
    library_repo: LibraryRepository,
    discovery_repo: DiscoveryRepository,
) -> DiscoveryResponse:
    """
    Handle latent space refinement using centroids as steering vectors.
    """
    # 1. Fetch Centroids
    centroids = await discovery_repo.get_all_centroids()

    # 2. Vector Math: Apply steering to base vector
    base = np.array(request.base_vector)
    zero = np.zeros(512)

    # Get centroids with zero-vector fallback
    c_electronic = np.array(centroids.get("electronic", zero))
    c_acoustic = np.array(centroids.get("acoustic", zero))
    c_hiphop = np.array(centroids.get("hiphop", zero))
    c_ambient = np.array(centroids.get("ambient", zero))
    c_global = np.array(centroids.get("global", zero))
    c_reggae = np.array(centroids.get("reggae", zero))

    # Steer
    refined = base.copy()

    # Axis 1: Digital vs. Organic
    if request.digital_organic != 0:
        refined += (c_electronic - c_acoustic) * request.digital_organic

    # Axis 2: Energy
    if request.energy != 0:
        refined += (c_hiphop - c_ambient) * request.energy

    # Axis 3: Urban Identity
    if request.urban != 0:
        refined += (c_hiphop - c_global) * request.urban

    # Axis 4: Bass Culture
    if request.bass != 0:
        refined += (c_reggae - c_global) * request.bass

    # 3. Perform search with refined vector
    refined_list = refined.tolist()
    candidates = await library_repo.search_semantic_by_vector(
        refined_list, limit=settings.SIMILAR_TRACKS_LIMIT
    )

    if not candidates:
        # Should be unlikely with a valid base vector, but possible
        return DiscoveryResponse(
            results=ScoredTrackList(tracks=[]),
            query_vector=refined_list,
        )

    # 4. Filter and Return
    results = _filter_diverse_results(candidates, settings.SIMILAR_TRACKS_RETURNED)

    return DiscoveryResponse(
        results=ScoredTrackList(tracks=results),
        query_vector=refined_list,
    )
