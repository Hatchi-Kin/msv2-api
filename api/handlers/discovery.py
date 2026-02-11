from api.core.config import settings
from api.core.exceptions import NotFoundException
from api.models.discovery import DiscoveryResponse, ScoredTrack, ScoredTrackList
from api.repositories.inference import InferenceRepository
from api.repositories.library import LibraryRepository


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
    # Using the same limit constant as similarity search for consistency
    candidates = await library_repo.search_semantic_by_vector(
        embedding_resp.embedding, limit=settings.SIMILAR_TRACKS_LIMIT
    )

    if not candidates:
        raise NotFoundException("Discovery matches", query)

    # 3. Apply Diversity Filter (Max 1 track per artist_folder)
    seen_artists = set()
    filtered_results = []

    for track, distance in candidates:
        if track.artist_folder not in seen_artists:
            filtered_results.append(ScoredTrack(track=track, similarity_score=distance))
            seen_artists.add(track.artist_folder)

        if len(filtered_results) >= settings.SIMILAR_TRACKS_RETURNED:
            break

    # 4. Wrap and Return
    return DiscoveryResponse(
        results=ScoredTrackList(tracks=filtered_results),
        query_vector=embedding_resp.embedding,
    )
