from typing import Optional, Dict, Any, List

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

    async def search_track(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
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
                else:
                    logger.warning(
                        f"Failed to get audio features for {track_id}: {features_res.status_code} {features_res.text}"
                    )
                    features = {}

                # 3. Get Artist (for Genres)
                artist_id = track["artists"][0]["id"]
                artist_res = await client.get(
                    f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers
                )
                artist_data = artist_res.json() if artist_res.status_code == 200 else {}

                return {
                    "spotify_id": track_id,
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "release_date": track["album"]["release_date"],
                    "popularity": track["popularity"],
                    "genres": artist_data.get("genres", []),
                    "bpm": features.get("tempo"),
                    "energy": features.get("energy"),
                    "danceability": features.get("danceability"),
                    "valence": features.get("valence"),
                    "key": features.get("key"),
                    "mode": features.get("mode"),
                    # Additional niche features
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

    # ==================== NEW METHODS BELOW ====================

    async def get_track_analysis(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed audio analysis - SUPER technical and niche!
        Includes sections, segments, bars, beats, tatums, pitch, timbre analysis.
        This is the most technical endpoint Spotify offers.
        """
        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/audio-analysis/{track_id}",
                    headers=headers,
                    timeout=30.0,  # This endpoint can be slow
                )

                if response.status_code == 200:
                    analysis = response.json()

                    # Extract the most interesting parts
                    return {
                        "duration": analysis.get("track", {}).get("duration"),
                        "num_samples": analysis.get("track", {}).get("num_samples"),
                        "sections": [
                            {
                                "start": s.get("start"),
                                "duration": s.get("duration"),
                                "loudness": s.get("loudness"),
                                "tempo": s.get("tempo"),
                                "key": s.get("key"),
                                "mode": s.get("mode"),
                                "time_signature": s.get("time_signature"),
                            }
                            for s in analysis.get("sections", [])
                        ],
                        "num_bars": len(analysis.get("bars", [])),
                        "num_beats": len(analysis.get("beats", [])),
                        "num_tatums": len(
                            analysis.get("tatums", [])
                        ),  # Sub-beat units!
                        "segments_count": len(analysis.get("segments", [])),
                        # Sample first segment for detailed timbre/pitch
                        "sample_segment": (
                            analysis.get("segments", [{}])[0]
                            if analysis.get("segments")
                            else {}
                        ),
                    }
                else:
                    logger.warning(
                        f"Failed to get track analysis: {response.status_code}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Track analysis failed: {e}")
            return None

    async def get_recommendations(
        self, seed_track_id: str, limit: int = 5, **target_features
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get recommendations based on a track.
        Can fine-tune with target audio features like:
        target_energy=0.8, target_danceability=0.6, etc.
        """
        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            params = {"seed_tracks": seed_track_id, "limit": limit}
            params.update(target_features)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.spotify.com/v1/recommendations",
                    params=params,
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "id": track["id"],
                            "name": track["name"],
                            "artist": track["artists"][0]["name"],
                            "popularity": track["popularity"],
                        }
                        for track in data.get("tracks", [])
                    ]
                else:
                    logger.warning(
                        f"Failed to get recommendations: {response.status_code}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Recommendations failed: {e}")
            return None

    async def get_artist_top_tracks(
        self, artist_id: str, market: str = "US"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get an artist's top 10 most popular tracks.
        """
        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
                    params={"market": market},
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "id": track["id"],
                            "name": track["name"],
                            "popularity": track["popularity"],
                            "album": track["album"]["name"],
                        }
                        for track in data.get("tracks", [])
                    ]
                else:
                    return None

        except Exception as e:
            logger.error(f"Top tracks lookup failed: {e}")
            return None

    async def get_related_artists(
        self, artist_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get artists similar to the given artist.
        Great for discovery!
        """
        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/artists/{artist_id}/related-artists",
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "id": artist["id"],
                            "name": artist["name"],
                            "genres": artist.get("genres", []),
                            "popularity": artist["popularity"],
                            "followers": artist["followers"]["total"],
                        }
                        for artist in data.get("artists", [])
                    ]
                else:
                    return None

        except Exception as e:
            logger.error(f"Related artists lookup failed: {e}")
            return None

    async def get_album_tracks(self, album_id: str) -> Optional[Dict[str, Any]]:
        """
        Get all tracks from an album.
        Useful to see the track's context within the album.
        """
        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/albums/{album_id}", headers=headers
                )

                if response.status_code == 200:
                    album = response.json()
                    return {
                        "id": album["id"],
                        "name": album["name"],
                        "release_date": album["release_date"],
                        "total_tracks": album["total_tracks"],
                        "popularity": album.get("popularity"),
                        "tracks": [
                            {
                                "id": track["id"],
                                "name": track["name"],
                                "track_number": track["track_number"],
                                "duration_ms": track["duration_ms"],
                            }
                            for track in album.get("tracks", {}).get("items", [])
                        ],
                    }
                else:
                    return None

        except Exception as e:
            logger.error(f"Album tracks lookup failed: {e}")
            return None

    async def get_artist_albums(
        self, artist_id: str, include_groups: str = "album,single", limit: int = 20
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get an artist's discography.
        include_groups can be: album, single, appears_on, compilation
        """
        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/artists/{artist_id}/albums",
                    params={"include_groups": include_groups, "limit": limit},
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "id": album["id"],
                            "name": album["name"],
                            "release_date": album["release_date"],
                            "total_tracks": album["total_tracks"],
                            "album_type": album["album_type"],
                        }
                        for album in data.get("items", [])
                    ]
                else:
                    return None

        except Exception as e:
            logger.error(f"Artist albums lookup failed: {e}")
            return None

    async def get_multiple_tracks_features(
        self, track_ids: List[str]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get audio features for multiple tracks at once (up to 100).
        Efficient for batch processing!
        """
        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            # Spotify allows max 100 IDs
            track_ids = track_ids[:100]

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.spotify.com/v1/audio-features",
                    params={"ids": ",".join(track_ids)},
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("audio_features", [])
                else:
                    return None

        except Exception as e:
            logger.error(f"Batch features lookup failed: {e}")
            return None

    def interpret_audio_features(self, features: Dict[str, Any]) -> Dict[str, str]:
        """
        Helper method to interpret audio features in human-readable terms.
        Makes your agent more conversational!
        """
        interpretations = {}

        # Energy interpretation
        energy = features.get("energy", 0)
        if energy > 0.8:
            interpretations["energy_desc"] = "very energetic and intense"
        elif energy > 0.6:
            interpretations["energy_desc"] = "moderately energetic"
        elif energy > 0.4:
            interpretations["energy_desc"] = "laid-back"
        else:
            interpretations["energy_desc"] = "calm and relaxed"

        # Valence (happiness) interpretation
        valence = features.get("valence", 0.5)
        if valence > 0.7:
            interpretations["mood"] = "happy and upbeat"
        elif valence > 0.5:
            interpretations["mood"] = "positive"
        elif valence > 0.3:
            interpretations["mood"] = "melancholic"
        else:
            interpretations["mood"] = "sad or dark"

        # Danceability
        dance = features.get("danceability", 0)
        if dance > 0.8:
            interpretations["dance"] = "extremely danceable"
        elif dance > 0.6:
            interpretations["dance"] = "danceable"
        else:
            interpretations["dance"] = "not very danceable"

        # Acousticness
        acoustic = features.get("acousticness", 0)
        if acoustic > 0.7:
            interpretations["acoustic"] = "mostly acoustic"
        elif acoustic > 0.3:
            interpretations["acoustic"] = "blend of acoustic and electric"
        else:
            interpretations["acoustic"] = "heavily produced/electric"

        # Key interpretation
        key_map = {
            0: "C",
            1: "C♯/D♭",
            2: "D",
            3: "D♯/E♭",
            4: "E",
            5: "F",
            6: "F♯/G♭",
            7: "G",
            8: "G♯/A♭",
            9: "A",
            10: "A♯/B♭",
            11: "B",
        }
        key = features.get("key")
        mode = features.get("mode")
        if key is not None and mode is not None:
            key_name = key_map.get(key, "unknown")
            mode_name = "major" if mode == 1 else "minor"
            interpretations["key"] = f"{key_name} {mode_name}"

        # BPM interpretation
        bpm = features.get("tempo")
        if bpm:
            if bpm < 80:
                interpretations["tempo_desc"] = "slow tempo"
            elif bpm < 120:
                interpretations["tempo_desc"] = "moderate tempo"
            elif bpm < 140:
                interpretations["tempo_desc"] = "upbeat tempo"
            else:
                interpretations["tempo_desc"] = "fast tempo"

        return interpretations
