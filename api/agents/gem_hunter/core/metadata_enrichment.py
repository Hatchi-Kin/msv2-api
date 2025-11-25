"""Metadata enrichment logic - enrich tracks with Spotify data."""

import asyncio
from typing import List
from api.core.logger import logger


async def enrich_tracks_parallel(
    tracks: List[dict], enrich_func, repo
) -> List[dict]:
    """Enrich multiple tracks in parallel for speed.

    Instead of processing tracks one-by-one (slow), we enrich all of them
    simultaneously using asyncio.gather(). This reduces total time from
    15-25s to 3-5s for 5 tracks.

    Args:
        tracks: List of track dictionaries to enrich
        enrich_func: The enrichment function to call (enrich_track_metadata)
        repo: Repository instance for database operations

    Returns:
        List of enriched track dictionaries
    """

    async def enrich_single_track(track: dict) -> dict:
        """Enrich a single track, handling errors gracefully."""
        # Check if track needs enrichment (missing key metadata)
        needs_enrichment = not all(
            [
                track.get("bpm"),
                track.get("energy"),
                track.get("genre") or track.get("top_5_genres"),
            ]
        )

        if needs_enrichment:
            logger.info(f"Enriching: {track.get('artist')} - {track.get('title')}")
            try:
                # Pass existing genres to skip artist lookup if we have them
                existing_genres = track.get("genre") or track.get("top_5_genres")

                new_data = await enrich_func(
                    track["id"],
                    track["artist"],
                    track["title"],
                    repo,
                    existing_genres=existing_genres,
                )
                if "error" not in new_data:
                    track.update(new_data)
                    logger.info(f"✅ Enriched: {track.get('title')}")
                else:
                    logger.warning(f"⚠️  Could not enrich: {track.get('title')}")
            except Exception as e:
                logger.warning(f"⚠️  Enrichment failed for {track.get('title')}: {e}")
        else:
            logger.info(f"✓ Already has metadata: {track.get('title')}")

        return track

    # Enrich all tracks in parallel
    enriched = await asyncio.gather(
        *[enrich_single_track(t) for t in tracks],
        return_exceptions=False,  # Let exceptions bubble up
    )

    return list(enriched)


def check_needs_enrichment(track: dict) -> bool:
    """Check if a track needs metadata enrichment.
    
    Args:
        track: Track dictionary
        
    Returns:
        True if track is missing key metadata
    """
    return not all(
        [
            track.get("bpm"),
            track.get("energy"),
            track.get("genre") or track.get("top_5_genres"),
        ]
    )
