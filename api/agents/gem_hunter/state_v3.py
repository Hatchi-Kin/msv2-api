"""State definitions for Music Curator Agent v3 (Supervisor Pattern)."""

from typing import TypedDict, List, Optional, Dict, Any

class Track(TypedDict):
    """Track with all metadata."""
    id: str
    title: str
    artist: str
    album: Optional[str]
    uri: str
    distance: float  # Similarity score from vector search
    bpm: Optional[float]
    energy: Optional[float]
    danceability: Optional[float]
    valence: Optional[float]
    genres: List[str]
    reason: Optional[str]  # LLM-generated pitch (added in present_results)

class AgentState(TypedDict):
    """Complete agent state for supervisor pattern."""
    
    # --- Input ---
    playlist_id: str
    user_id: str
    
    # --- Flow Control Flags ---
    playlist_analyzed: bool
    vibe_choice: Optional[str]  # "similar" | "chill" | "energy" | "surprise"
    search_iteration: int
    knowledge_checked: bool
    results_presented: bool
    
    # --- Data State ---
    playlist_profile: Optional[Dict[str, Any]]  # {avg_bpm, avg_energy, top_genres, description}
    candidate_tracks: List[Track]
    quality_assessment: Optional[Dict[str, Any]]  # {sufficient, quality_score, recommendation}
    known_artists: List[str]
    
    # --- Supervisor Control ---
    next_action: str  # Tool name or "END"
    supervisor_reasoning: str
    tool_parameters: Dict[str, Any]
    action_history: List[str]  # Last 3 actions for loop detection
    iteration_count: int
    
    # --- UI State ---
    ui_state: Optional[Dict[str, Any]]  # {message, options, cards}
    
    # --- Error Handling ---
    error: Optional[str]
