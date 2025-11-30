from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Track(BaseModel):
    """Track metadata model."""

    id: int
    filename: str
    filepath: str
    relative_path: str
    album_folder: Optional[str] = None
    artist_folder: Optional[str] = None
    filesize: Optional[float] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    tracknumber: Optional[int] = None
    genre: Optional[str] = None
    top_5_genres: Optional[str] = None
    created_at: datetime
    embedding_512_vector: Optional[List[float]] = None
    
    # Audio Features
    bpm: Optional[float] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    valence: Optional[float] = None
    key: Optional[int] = None
    brightness: Optional[float] = None
    harmonic_ratio: Optional[float] = None


class ArtistList(BaseModel):
    artists: List[str]
    total: int


class AlbumList(BaseModel):
    albums: List[str]


class TrackList(BaseModel):
    tracks: List[Track]


class SimilarTrack(BaseModel):
    track: Track
    similarity_score: float


class SimilarTrackList(BaseModel):
    tracks: List[SimilarTrack]


class FavoritesList(BaseModel):
    tracks: List[Track]
    total: int


class PlaylistSummary(BaseModel):
    id: int
    name: str
    track_count: int
    created_at: datetime
    updated_at: datetime


class PlaylistsList(BaseModel):
    playlists: List[PlaylistSummary]


class PlaylistDetail(BaseModel):
    id: int
    name: str
    tracks: List[Track]
    created_at: datetime
    updated_at: datetime


class CreatePlaylistRequest(BaseModel):
    name: str


class UpdatePlaylistRequest(BaseModel):
    name: str
