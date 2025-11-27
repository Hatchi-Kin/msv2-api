from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class TrackCard(BaseModel):
    """Full track object with agent's pitch/reason.

    Includes all MegasetTrack fields so the frontend can use
    the same card components and player functionality.
    """

    # Core identification
    id: int
    filename: str
    filepath: str
    relative_path: str

    # Metadata
    album_folder: Optional[str] = None
    artist_folder: Optional[str] = None
    filesize: Optional[int] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    tracknumber: Optional[int] = None
    genre: Optional[str] = None
    top_5_genres: Optional[str] = None
    created_at: Optional[str] = None

    # Agent-specific field
    reason: str  # The "Pitch" - why this track is recommended


class ButtonOption(BaseModel):
    id: str  # e.g., "add_track_123"
    label: str
    action: str  # "add", "search_more", "reject"
    payload: Dict[str, Any]


class UIState(BaseModel):
    message: str
    understanding: Optional[str] = None
    selection: Optional[str] = None
    cards: List[TrackCard] = []
    options: List[ButtonOption] = []
    fun_fact: Optional[str] = None  # Fact to display during the *next* loading screen


class AgentState(TypedDict, total=False):
    # Standard LangGraph message history (for chat context if needed)
    messages: Annotated[List[dict], add_messages]

    # Context
    playlist_id: int
    user_preferences: str

    # Working Memory
    centroid: Optional[List[float]]
    candidate_tracks: List[dict]  # Raw track dicts from DB
    enriched_tracks: List[dict]  # Tracks with Spotify data

    # Output State (what the UI renders)
    ui_state: Optional[dict]  # Changed from UIState to dict for serialization

    # Fun facts to display during loading
    fun_fact_1: Optional[str]  # Shown during first wait (after user answers Q1)
    fun_fact_2: Optional[str]  # Shown during second wait (after user answers Q2)

    # Loop Control
    excluded_ids: List[int]
    excluded_artists: List[str]  # Artists user already knows
    known_artists: List[str]  # Alias for excluded_artists (from user input)
    next_step: Optional[str]  # For conditional edges

    # Interaction Flags
    knowledge_checked: bool
    vibe_checked: bool
    vibe_choice: Optional[str]
