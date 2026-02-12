from typing import List

from pydantic import BaseModel

from api.models.library import Track


class ScoredTrack(BaseModel):
    """
    A track coupled with a relevance score.
    Used for both:
    1. Similarity Search (Audio-to-Audio): score is the distance/similarity between song vectors.
    2. Semantic Search (Text-to-Audio): score is the distance/similarity between text and audio vectors.
    """

    track: Track
    similarity_score: float


class ScoredTrackList(BaseModel):
    """List of tracks filtered/sorted by similarity or semantic relevance."""

    tracks: List[ScoredTrack]


class DiscoveryResponse(BaseModel):
    """The final response sent to the frontend for a discovery search."""

    results: ScoredTrackList
    query_vector: List[float]


class DiscoveryRefineRequest(BaseModel):
    """Request for refining discovery results using latent space manipulation."""

    base_vector: List[float]
    digital_organic: float = 0.0  # -1.0 (Organic) to 1.0 (Digital)
    energy: float = 0.0  # -1.0 (Ambient) to 1.0 (Energy)
    urban: float = 0.0  # -1.0 to 1.0 (Hip-Hop Boost)
    bass: float = 0.0  # -1.0 to 1.0 (Reggae Boost)
