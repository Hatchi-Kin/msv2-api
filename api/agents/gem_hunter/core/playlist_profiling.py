"""Playlist profiling logic - pure functions for analyzing playlist characteristics."""

from typing import List, Dict, Any
from collections import Counter


def build_playlist_profile(tracks: List[dict]) -> Dict[str, Any]:
    """Build a statistical profile of the playlist.

    Args:
        tracks: List of track dictionaries with metadata

    Returns:
        Dictionary containing:
        - track_count: Number of tracks
        - genres: Top genres
        - artists: Top artists
        - avg_bpm: Average BPM
        - avg_energy: Average energy (0-100)
        - sample_tracks: Sample track names
    """
    if not tracks:
        return {
            "track_count": 0,
            "genres": [],
            "artists": [],
            "avg_bpm": 0,
            "avg_energy": 0,
            "sample_tracks": [],
        }

    # Extract genres (handle both 'genre' and 'top_5_genres')
    genres = []
    for t in tracks:
        if t.get("genre"):
            genres.append(t["genre"])
        elif t.get("top_5_genres"):
            # Take first genre from comma-separated list
            first_genre = t["top_5_genres"].split(",")[0].strip()
            if first_genre:
                genres.append(first_genre)

    # Get top genres
    genre_counts = Counter(genres)
    top_genres = [g for g, _ in genre_counts.most_common(5)]

    # Get unique artists
    artists = list({t["artist"] for t in tracks if t.get("artist")})[:10]

    # Calculate averages (if available)
    bpms = [t.get("bpm") for t in tracks if t.get("bpm")]
    energies = [t.get("energy") for t in tracks if t.get("energy")]

    avg_bpm = sum(bpms) / len(bpms) if bpms else None
    avg_energy = sum(energies) / len(energies) if energies else None

    # Sample tracks for context
    sample_tracks = [
        f"{t['artist']} - {t['title']}"
        for t in tracks[:5]
        if t.get("artist") and t.get("title")
    ]

    return {
        "track_count": len(tracks),
        "genres": top_genres,
        "artists": artists[:5],  # Top 5 artists
        "avg_bpm": round(avg_bpm) if avg_bpm else None,
        "avg_energy": round(avg_energy * 100) if avg_energy else None,
        "sample_tracks": sample_tracks,
    }
