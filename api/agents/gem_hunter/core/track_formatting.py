"""Track formatting logic - create UI-ready track cards."""

from typing import List, Dict

from api.agents.gem_hunter.state import TrackCard


def create_track_cards(tracks: List[dict], pitches: Dict[int, str]) -> List[TrackCard]:
    """Create TrackCard objects with full metadata.

    Args:
        tracks: List of track dictionaries
        pitches: Dictionary mapping track_id to pitch text

    Returns:
        List of TrackCard objects ready for UI
    """
    cards = []
    for t in tracks:
        # Convert types to match Pydantic schema
        filesize = t.get("filesize")
        if filesize is not None and isinstance(filesize, float):
            filesize = int(filesize)

        created_at = t.get("created_at")
        if created_at is not None and hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()

        cards.append(
            TrackCard(
                # Core identification
                id=t["id"],
                filename=t.get("filename", ""),
                filepath=t.get("filepath", ""),
                relative_path=t.get("relative_path", ""),
                # Metadata
                album_folder=t.get("album_folder"),
                artist_folder=t.get("artist_folder"),
                filesize=filesize,
                title=t.get("title"),
                artist=t.get("artist"),
                album=t.get("album"),
                year=t.get("year"),
                tracknumber=t.get("tracknumber"),
                genre=t.get("genre"),
                top_5_genres=t.get("top_5_genres"),
                created_at=created_at,
                # Agent-specific field
                reason=pitches.get(t["id"], "Recommended for you"),
                # Audio Features
                bpm=t.get("bpm"),
                energy=t.get("energy"),
                valence=t.get("valence"),
                danceability=t.get("danceability"),
                spotify_id=t.get("spotify_id"),
            )
        )
    return cards
