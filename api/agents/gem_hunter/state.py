from typing import List, Optional, Dict, Any, TypedDict, Annotated
from operator import add

class Track(TypedDict):
    id: str
    title: str
    artist: str
    album: str
    uri: str
    image_url: Optional[str]
    preview_url: Optional[str]
    bpm: Optional[float]
    energy: Optional[float]
    danceability: Optional[float]
    valence: Optional[float]
    genres: List[str]
    explanation: Optional[str]  # Why this track was chosen

class UIState(TypedDict):
    message: str
    options: List[Dict[str, Any]]
    cards: Optional[List[Dict[str, Any]]]
    thought_process: List[str]

class AgentState(TypedDict):
    # --- Input ---
    playlist_id: str
    user_id: str
    
    # --- Flow Control Flags ---
    playlist_analyzed: bool
    vibe_selected: bool
    search_done: bool
    enriched: bool
    filtered: bool
    knowledge_checked: bool
    knowledge_search_attempted: bool
    results_presented: bool
    
    # --- Data State ---
    playlist_profile: Dict[str, Any]  # Stats: avg_bpm, genres, etc.
    vibe_choice: Optional[str]        # User's selected vibe (e.g., "more_energy")
    constraints: Dict[str, Any]       # Search constraints (min_bpm, etc.)
    
    candidate_tracks: List[Track]     # Raw search results
    enriched_tracks: List[Track]      # Tracks with full metadata
    final_tracks: List[Track]         # Filtered & Knowledge-checked tracks
    
    known_artists: Annotated[List[str], add] # Accumulate known artists
    excluded_artists: List[str]       # Artists to exclude from next search
    
    # --- UI State ---
    ui_state: UIState
    
    # --- Internal ---
    iteration_count: int
    error: Optional[str]
