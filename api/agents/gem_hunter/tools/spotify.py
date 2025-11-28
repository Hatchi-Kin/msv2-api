import time
from typing import Optional, Dict, Any

import httpx

from api.core.logger import logger
from api.core.config import settings


class SpotifyClient:
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.token = None
        self.token_expiry = 0

    async def _get_token(self) -> str:
        """Get or refresh access token using refresh token (user auth) or client credentials."""
        if self.token:
            # TODO: Check expiry logic if needed, for now simple check
            return self.token

        async with httpx.AsyncClient() as client:
            # Try refresh token first (user auth - has access to audio features)
            refresh_token = getattr(settings, "SPOTIFY_REFRESH_TOKEN", None)

            if refresh_token:
                # Use refresh token to get new access token
                response = await client.post(
                    "https://accounts.spotify.com/api/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                    auth=(self.client_id, self.client_secret),
                )
                response.raise_for_status()
                data = response.json()
                self.token = data["access_token"]
                # Spotify returns expires_in (seconds)
                self.token_expiry = time.time() + data.get("expires_in", 3600)
                logger.info(
                    "✅ Using Spotify user authentication (audio features enabled)"
                )
                return self.token
            else:
                logger.warning(
                    "⚠️ Using client credentials (audio features disabled). "
                    "Add SPOTIFY_REFRESH_TOKEN to .env for full access."
                )
                response = await client.post(
                    "https://accounts.spotify.com/api/token",
                    data={"grant_type": "client_credentials"},
                    auth=(self.client_id, self.client_secret),
                )
                response.raise_for_status()
                data = response.json()
                self.token = data["access_token"]
                self.token_expiry = time.time() + data.get("expires_in", 3600)
                return self.token

    async def search_track(
        self, artist: str, title: str, skip_artist_if_has_genres: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a track and return its basic metadata and IDs.
        DOES NOT fetch audio features or artist details (use batch methods for that).
        """
        if not self.client_id or not self.client_secret:
            logger.warning("Spotify credentials not set. Skipping lookup.")
            return None

        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            # Search for the track
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

                return {
                    "spotify_id": track["id"],
                    "artist_id": track["artists"][0]["id"],
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "release_date": track["album"]["release_date"],
                    "popularity": track["popularity"],
                    "duration_ms": track["duration_ms"],
                    "explicit": track["explicit"],
                    "preview_url": track.get("preview_url"),
                }

        except Exception as e:
            logger.error(f"Spotify lookup failed: {e}")
            return None

    async def get_audio_features_batch(self, track_ids: list[str]) -> Dict[str, Any]:
        """Fetch audio features for multiple tracks in one call."""
        if not track_ids or not self.client_id:
            return {}

        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            # Spotify allows max 100 IDs per call
            # We assume track_ids is small enough (<100) for this agent
            ids_str = ",".join(track_ids[:100])

            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "https://api.spotify.com/v1/audio-features",
                    params={"ids": ids_str},
                    headers=headers,
                )

                if res.status_code == 429:
                    logger.warning(
                        "⚠️ Spotify Rate Limit Hit (429) in batch audio features"
                    )
                    return {}

                res.raise_for_status()
                data = res.json()

                # Map id -> features
                features_map = {}
                for item in data.get("audio_features", []):
                    if item:
                        features_map[item["id"]] = item

                return features_map

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Batch audio features failed: {e.response.status_code} - {e.response.text}"
            )
            return {}
        except Exception as e:
            logger.error(f"Batch audio features failed: {e}")
            return {}

    async def get_artists_batch(self, artist_ids: list[str]) -> Dict[str, Any]:
        """Fetch artist details (genres) for multiple artists in one call."""
        if not artist_ids or not self.client_id:
            return {}

        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            # Spotify allows max 50 IDs per call
            ids_str = ",".join(artist_ids[:50])

            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "https://api.spotify.com/v1/artists",
                    params={"ids": ids_str},
                    headers=headers,
                )

                if res.status_code == 429:
                    logger.warning("⚠️ Spotify Rate Limit Hit (429) in batch artists")
                    return {}

                res.raise_for_status()
                data = res.json()

                # Map id -> artist data
                artists_map = {}
                for item in data.get("artists", []):
                    if item:
                        artists_map[item["id"]] = item

                return artists_map

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Batch artists failed: {e.response.status_code} - {e.response.text}"
            )
            return {}
        except Exception as e:
            logger.error(f"Batch artists failed: {e}")
            return {}
