"""Preference filtering logic - filter tracks based on user preferences."""

from typing import List


def filter_by_known_artists(
    candidates: List[dict], known_artists: List[str]
) -> List[dict]:
    """Filter out tracks by artists the user already knows.

    Args:
        candidates: List of candidate track dictionaries
        known_artists: List of artist names to exclude

    Returns:
        Filtered list of tracks
    """
    if not known_artists:
        return candidates

    return [c for c in candidates if c.get("artist") not in known_artists]


def get_unique_artists(tracks: List[dict], limit: int = 5) -> List[str]:
    """Extract unique artist names from tracks.

    Args:
        tracks: List of track dictionaries
        limit: Maximum number of artists to return

    Returns:
        List of unique artist names
    """
    return list({t["artist"] for t in tracks if t.get("artist")})[:limit]
