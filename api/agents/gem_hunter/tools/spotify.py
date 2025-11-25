import httpx
from typing import Optional, Dict, Any
from api.core.logger import logger
from api.core.config import settings


class SpotifyClient:
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.token = None
        self.token_expiry = 0

    async def _get_token(self) -> str:
        """Get or refresh Client Credentials token."""
        if self.token:
            # TODO: Check expiry logic if needed, for now simple check
            return self.token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            return self.token

    async def search_track(
        self, artist: str, title: str, skip_artist_if_has_genres: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a track and return its metadata (including audio features if possible).
        """
        if not self.client_id or not self.client_secret:
            logger.warning("Spotify credentials not set. Skipping lookup.")
            return None

        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            # 1. Search for the track
            query = f"track:{title} artist:{artist}"
            async with httpx.AsyncClient() as client:
                search_res = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": query, "type": "track", "limit": 1},
                    headers=headers,
                )
                search_res.raise_for_status()
                data = search_res.json()

                items = data.get("tracks", {}).get("items", [])
                if not items:
                    return None

                track = items[0]
                track_id = track["id"]

                # 2. Get Audio Features (BPM, Key, etc.)
                features_res = await client.get(
                    f"https://api.spotify.com/v1/audio-features/{track_id}",
                    headers=headers,
                )
                if features_res.status_code == 200:
                    features = features_res.json()
                elif features_res.status_code == 403:
                    logger.warning(
                        f"⚠️  Spotify API returned 403 Forbidden for audio features of '{artist} - {title}' (track_id: {track_id}). "
                        f"This can occur due to: rate limiting, regional restrictions, or content access policies. "
                        f"Continuing with basic metadata only."
                    )
                    features = {}
                else:
                    logger.warning(
                        f"Failed to get audio features for {track_id}: {features_res.status_code} {features_res.text}"
                    )
                    features = {}

                # 3. Get Artist (for Genres) - skip if we already have genre data
                artist_genres = []
                if not skip_artist_if_has_genres:
                    artist_id = track["artists"][0]["id"]
                    artist_res = await client.get(
                        f"https://api.spotify.com/v1/artists/{artist_id}",
                        headers=headers,
                    )
                    artist_data = (
                        artist_res.json() if artist_res.status_code == 200 else {}
                    )
                    artist_genres = artist_data.get("genres", [])
                else:
                    logger.info(
                        f"⚡ Skipping artist lookup (already has genres): {artist} - {title}"
                    )

                return {
                    "spotify_id": track_id,
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "release_date": track["album"]["release_date"],
                    "popularity": track["popularity"],
                    "duration_ms": track["duration_ms"],
                    "explicit": track["explicit"],
                    "preview_url": track.get("preview_url"),
                    # Spotify genres (only if we fetched artist)
                    "spotify_genres": artist_genres,
                    # Audio features
                    "bpm": features.get("tempo"),
                    "key": features.get("key"),
                    "mode": features.get("mode"),
                    "energy": features.get("energy"),
                    "danceability": features.get("danceability"),
                    "valence": features.get("valence"),
                    "acousticness": features.get("acousticness"),
                    "instrumentalness": features.get("instrumentalness"),
                    "liveness": features.get("liveness"),
                    "speechiness": features.get("speechiness"),
                    "loudness": features.get("loudness"),
                    "time_signature": features.get("time_signature"),
                }

        except Exception as e:
            logger.error(f"Spotify lookup failed: {e}")
            return None
