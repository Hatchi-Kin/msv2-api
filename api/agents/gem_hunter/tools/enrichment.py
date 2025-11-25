from api.agents.gem_hunter.tools.spotify import SpotifyClient
from api.repositories.library import LibraryRepository
from api.core.logger import logger


async def enrich_track_metadata(
    track_id: int,
    artist: str,
    title: str,
    repo: LibraryRepository,
    existing_genres: str = None,
) -> dict:
    """
    Tool to look up a track on Spotify and update the local database with missing info.
    Returns the enriched data.

    Args:
        existing_genres: Existing genre data to skip artist lookup if present
    """
    logger.info(f"Enriching metadata for: {artist} - {title}")

    spotify = SpotifyClient()
    data = await spotify.search_track(
        artist, title, skip_artist_if_has_genres=bool(existing_genres)
    )

    if not data:
        logger.warning(f"No data found on Spotify for: {artist} - {title}")
        return {"error": "Not found"}

    # -------------------------------------------------------------------------
    # FUTURE IMPLEMENTATION NOTES:
    # -------------------------------------------------------------------------
    # We deliberately DO NOT update the database here for two reasons:
    #
    # 1. DATA PROTECTION:
    #    The 'top_5_genres' column is populated by our OpenL3 analysis and is
    #    considered "precious" ground truth. Overwriting it with Spotify genres
    #    would degrade our data quality.
    #
    # 2. SCHEMA EVOLUTION:
    #    To properly utilize Spotify data, we should migrate the DB schema to include:
    #    - spotify_id: CRITICAL for linking and avoiding re-fetching.
    #    - bpm, key, mode: Musical features.
    #    - energy, danceability, valence: Audio features.
    #
    # Once 'spotify_id' is in the schema, we can check for existence before fetching.
    # -------------------------------------------------------------------------

    return data
