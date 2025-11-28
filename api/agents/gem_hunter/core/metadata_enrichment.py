"""Metadata enrichment logic - enrich tracks with Spotify data."""

from typing import List

import asyncio

from api.core.logger import logger
from api.agents.gem_hunter.tools.spotify import SpotifyClient


async def enrich_tracks_parallel(tracks: List[dict], enrich_func, repo) -> List[dict]:
    """Enrich multiple tracks in parallel using batch APIs.

    Optimized to avoid Spotify rate limits (429/403) by:
    1. Searching for track IDs in parallel (lightweight).
    2. Fetching audio features in a SINGLE batch call.
    3. Fetching artist genres in a SINGLE batch call.

    Args:
        tracks: List of track dictionaries to enrich
        enrich_func: DEPRECATED/UNUSED (kept for signature compatibility)
        repo: Repository instance (unused in this version but kept for compat)

    Returns:
        List of enriched track dictionaries
    """
    spotify = SpotifyClient()

    # 1. Identify tracks needing enrichment
    tracks_to_enrich = []
    for t in tracks:
        if check_needs_enrichment(t):
            tracks_to_enrich.append(t)

    if not tracks_to_enrich:
        return tracks

    logger.info(f"🎵 Batch enriching {len(tracks_to_enrich)} tracks...")

    # 2. Step 1: Search for Spotify IDs (Parallel)
    # We still need to search one-by-one to get the ID, but this is a lighter endpoint
    # and we can limit concurrency if needed, but usually search is fine.

    async def get_id(track):
        # Skip if we already have a spotify_id (future proofing)
        if track.get("spotify_id"):
            return track

        # Search
        res = await spotify.search_track(
            track["artist"],
            track["title"],
            skip_artist_if_has_genres=False,  # We'll fetch genres in batch later
        )

        if res:
            track.update(res)  # Updates with spotify_id, artist_id, etc.
        return track

    # Run searches
    await asyncio.gather(*[get_id(t) for t in tracks_to_enrich])

    # 3. Step 2: Batch Audio Features
    # Collect IDs for tracks that were successfully found
    track_ids = [t["spotify_id"] for t in tracks_to_enrich if t.get("spotify_id")]

    if track_ids:
        logger.info(f"📊 Fetching audio features for {len(track_ids)} tracks...")
        features_map = await spotify.get_audio_features_batch(track_ids)

        # Update tracks with features
        for track in tracks_to_enrich:
            sid = track.get("spotify_id")
            if sid and sid in features_map:
                f = features_map[sid]
                track.update(
                    {
                        "bpm": f.get("tempo"),
                        "key": f.get("key"),
                        "mode": f.get("mode"),
                        "energy": f.get("energy"),
                        "danceability": f.get("danceability"),
                        "valence": f.get("valence"),
                        "acousticness": f.get("acousticness"),
                        "instrumentalness": f.get("instrumentalness"),
                        "liveness": f.get("liveness"),
                        "speechiness": f.get("speechiness"),
                        "loudness": f.get("loudness"),
                        "time_signature": f.get("time_signature"),
                    }
                )

    # 4. Step 3: Batch Artist Genres
    # Collect Artist IDs for tracks that don't have genres yet
    artist_ids = []
    for t in tracks_to_enrich:
        # If we already have genres (from DB or elsewhere), skip
        if t.get("genre") or t.get("top_5_genres") or t.get("spotify_genres"):
            continue

        if t.get("artist_id"):
            artist_ids.append(t["artist_id"])

    # Deduplicate
    artist_ids = list(set(artist_ids))

    if artist_ids:
        logger.info(f"🎨 Fetching genres for {len(artist_ids)} artists...")
        artists_map = await spotify.get_artists_batch(artist_ids)

        # Update tracks with genres
        for track in tracks_to_enrich:
            aid = track.get("artist_id")
            if aid and aid in artists_map:
                genres = artists_map[aid].get("genres", [])
                track["spotify_genres"] = genres
                # Also populate 'genre' if empty, for fallback
                if not track.get("genre") and genres:
                    track["genre"] = genres[0]

    logger.info("✅ Batch enrichment complete.")
    return tracks


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
