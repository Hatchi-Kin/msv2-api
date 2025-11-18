from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class MegasetTrack(BaseModel):
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


class ArtistList(BaseModel):
    artists: List[str]


class AlbumList(BaseModel):
    albums: List[str]


class TrackList(BaseModel):
    tracks: List[MegasetTrack]


class SimilarTrack(BaseModel):
    track: MegasetTrack
    similarity_score: float


class SimilarTrackList(BaseModel):
    tracks: List[SimilarTrack]
