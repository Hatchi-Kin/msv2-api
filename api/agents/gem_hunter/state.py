"""State definitions for Music Curator Agent v3 (Supervisor Pattern)."""

from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field


class Track(BaseModel):
    """Track with all metadata."""

    id: str
    title: str
    artist: str
    album: Optional[str] = None
    uri: str
    distance: float  # Similarity score from vector search
    bpm: Optional[float] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    valence: Optional[float] = None
    genres: List[str] = Field(default_factory=list)
    reason: Optional[str] = None  # LLM-generated pitch (added in present_results)


class AgentState(BaseModel):
    """Complete agent state for supervisor pattern."""

    # --- Input ---
    playlist_id: str
    user_id: str

    # --- Flow Control Flags ---
    playlist_analyzed: bool = False
    vibe_choice: Optional[str] = None  # "similar" | "chill" | "energy" | "surprise"
    search_iteration: int = 0
    knowledge_checked: bool = False
    results_presented: bool = False

    # --- Data State ---
    playlist_profile: Optional[Dict[str, Any]] = (
        None  # {avg_bpm, avg_energy, top_genres, description}
    )
    candidate_tracks: List[Union[Track, Dict[str, Any]]] = Field(default_factory=list)
    quality_assessment: Optional[Dict[str, Any]] = (
        None  # {sufficient, quality_score, recommendation}
    )
    known_artists: List[str] = Field(default_factory=list)

    # --- Supervisor Control ---
    next_action: str = ""  # Tool name or "END"
    supervisor_reasoning: str = ""
    tool_parameters: Dict[str, Any] = Field(default_factory=dict)
    action_history: List[str] = Field(
        default_factory=list
    )  # Last 3 actions for loop detection
    iteration_count: int = 0

    # --- UI State ---
    ui_state: Optional[Dict[str, Any]] = None  # {message, options, cards}

    # --- Error Handling ---
    error: Optional[str] = None
