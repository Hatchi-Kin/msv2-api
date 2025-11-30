from typing import List, Dict, Any

import asyncpg

from api.repositories.library import LibraryRepository
from api.repositories.playlists import PlaylistsRepository
from api.models.library import Track


async def analyze_playlist_stats(
    pool: asyncpg.Pool, playlist_id: int
) -> Dict[str, Any]:
    """Get stats for a playlist."""
    repo = PlaylistsRepository(pool)
    return await repo.get_playlist_stats(playlist_id)


async def search_similar_tracks(
    pool: asyncpg.Pool,
    playlist_id: int,
    constraints: Dict[str, Any],
    exclude_ids: List[int],
    exclude_artists: List[str],
    limit: int = 30,
) -> List[Track]:
    """Find similar tracks using vector search."""
    playlist_repo = PlaylistsRepository(pool)
    library_repo = LibraryRepository(pool)

    # 1. Get centroid
    centroid = await playlist_repo.get_playlist_centroid(playlist_id)
    if not centroid:
        print("⚠️ No centroid found for playlist")
        return []

    print(f"🔍 Centroid Type: {type(centroid)}")
    print(f"🔍 Centroid Preview: {str(centroid)[:50]}...")

    # 2. Search
    return await library_repo.search_hidden_gems_with_filters(
        centroid=centroid,
        exclude_ids=exclude_ids,
        exclude_artists=exclude_artists,
        min_bpm=constraints.get("min_bpm", 0),
        max_bpm=constraints.get("max_bpm", 999),
        min_energy=constraints.get("min_energy", 0),
        max_energy=constraints.get("max_energy", 1.0),
        limit=limit,
    )


def filter_tracks_strict(
    tracks: List[Track], constraints: Dict[str, Any]
) -> List[Track]:
    """Apply strict filtering in memory (double check)."""
    filtered = []
    for t in tracks:
        # Check BPM
        if t.bpm is not None:
            if t.bpm < constraints.get("min_bpm", 0):
                continue
            if t.bpm > constraints.get("max_bpm", 999):
                continue

        # Check Energy
        if t.energy is not None:
            if t.energy < constraints.get("min_energy", 0):
                continue
            if t.energy > constraints.get("max_energy", 1.0):
                continue

        filtered.append(t)
    return filtered
