# Gem Hunter V2 - Implementation Specification

**Status:** 🏗️ In Progress  
**Branch:** `gem-hunter-rewrite`  
**Goal:** A robust, deterministic agent for finding hidden gems.

---

## 1. Core Philosophy

1.  **Deterministic Flow**: The main logic loop is HARD-CODED. The LLM does NOT decide the next step; the state machine does.
2.  **Explicit State**: Every decision is tracked by a boolean flag in `AgentState`.
3.  **Content-Only LLM**: The LLM is used *only* for generating text (descriptions, pitches) and interpreting fuzzy user input. It does *not* control the flow.

---

## 2. The Flow (State Machine)

The agent follows this strict linear path, with loops only for specific conditions:

1.  **START**
2.  **Analyze Playlist** (`analyze_playlist`)
    *   *Input:* `playlist_id`
    *   *Output:* `playlist_profile` (stats), `ui_state` (vibe options)
    *   *Transition:* -> **WAIT FOR USER** (Vibe Selection)
3.  **Search Tracks** (`search_tracks`)
    *   *Trigger:* User selects vibe
    *   *Input:* `vibe_choice`, `playlist_profile`
    *   *Output:* `candidate_tracks` (raw from DB)
    *   *Transition:* -> `enrich_tracks`
4.  **Enrich Tracks** (`enrich_tracks`)
    *   *Input:* `candidate_tracks`
    *   *Output:* `enriched_tracks` (metadata added)
    *   *Transition:* -> `filter_tracks`
5.  **Filter Tracks** (`filter_tracks`)
    *   *Input:* `enriched_tracks`, `constraints`
    *   *Output:* `final_tracks` (filtered list)
    *   *Transition:* -> `check_knowledge`
6.  **Check Knowledge** (`check_knowledge`)
    *   *Input:* `final_tracks`
    *   *Output:* `ui_state` (artist list)
    *   *Transition:* -> **WAIT FOR USER** (Artist Selection)
7.  **Process Knowledge** (`process_knowledge`)
    *   *Trigger:* User selects known artists
    *   *Logic:*
        *   If **All Known** (and first try): Reset & Re-Search (Loop to Step 3)
        *   If **All Known** (and second try): Proceed anyway
        *   If **Some/None Known**: Filter out known, Proceed
    *   *Transition:* -> `present_results` OR `search_tracks`
8.  **Present Results** (`present_results`)
    *   *Input:* `final_tracks` (unknown artists)
    *   *Output:* `ui_state` (final cards with pitches)
    *   *Transition:* -> **END**

---

## 3. Data Model (`AgentState`)

```python
class AgentState(TypedDict):
    # Inputs
    playlist_id: str
    user_id: str
    
    # Flow Flags (The "Brain")
    playlist_analyzed: bool      # Step 2 done?
    vibe_selected: bool          # User picked vibe?
    search_done: bool            # Step 3 done?
    enriched: bool               # Step 4 done?
    filtered: bool               # Step 5 done?
    knowledge_checked: bool      # Step 6 done?
    knowledge_search_attempted: bool # Did we re-search once?
    
    # Data
    playlist_profile: Dict       # {avg_bpm: 120, genres: [...]}
    vibe_choice: str             # "more_energy"
    constraints: Dict            # {min_bpm: 130}
    
    # Tracks
    candidate_tracks: List[Track] # Raw from DB
    enriched_tracks: List[Track]  # With metadata
    final_tracks: List[Track]     # Ready for user
    
    # Knowledge
    known_artists: List[str]      # Accumulated known artists
    excluded_artists: List[str]   # Exclude from search
    
    # UI
    ui_state: UIState             # Current message/options
```

---

## 4. Node Logic

### `analyze_playlist`
- **Goal:** Understand the starting point.
- **Logic:**
    1. Fetch last 20 tracks from playlist.
    2. Calc avg BPM, Energy, Top Genres.
    3. LLM: Generate 1-sentence description ("Upbeat pop with electronic elements").
    4. Generate UI Options based on stats (e.g., if High Energy -> offer "Chill" option).
- **State Update:** `playlist_analyzed=True`, `playlist_profile={...}`, `ui_state={...}`

### `search_tracks`
- **Goal:** Find candidates.
- **Logic:**
    1. Get playlist centroid (vector).
    2. Apply constraints from `vibe_choice` (e.g., if "Chill", max_energy=0.5).
    3. Vector Search: Find 50 nearest neighbors.
    4. Exclude `excluded_artists` and `known_artists`.
- **State Update:** `search_done=True`, `candidate_tracks=[...]`

### `enrich_tracks`
- **Goal:** Add metadata.
- **Logic:**
    1. (Currently) Pass-through since DB has data.
    2. (Future) Fetch Spotify images/previews.
- **State Update:** `enriched=True`, `enriched_tracks=[...]`

### `filter_tracks`
- **Goal:** Refine candidates.
- **Logic:**
    1. Apply strict audio filters (BPM, Energy) if `vibe_choice` dictates.
    2. Limit to top 10.
- **State Update:** `filtered=True`, `final_tracks=[...]`

### `check_knowledge`
- **Goal:** Identify known artists.
- **Logic:**
    1. Extract unique artists from `final_tracks`.
    2. Generate UI: "Do you know any of these? [Artist A] [Artist B]..."
- **State Update:** `knowledge_checked=True`, `ui_state={...}`

### `process_knowledge`
- **Goal:** Handle user input & edge cases.
- **Logic:**
    1. Add selected artists to `known_artists`.
    2. **Edge Case:** If User knows ALL artists:
        *   If `knowledge_search_attempted=False`:
            *   Set `excluded_artists += known_artists`
            *   Set `knowledge_search_attempted=True`
            *   **RESET:** `search_done=False`, `enriched=False`, `filtered=False`, `knowledge_checked=False`
            *   Return to `search_tracks`.
        *   Else: Proceed (warn user).
- **State Update:** `known_artists=[...]`, (flags reset if looping)

### `present_results`
- **Goal:** Sell the hidden gems.
- **Logic:**
    1. Take top 5-10 unknown tracks.
    2. LLM: Generate "Pitch" for each ("Like [Artist] but with [Feature]").
    3. LLM: Generate "Justification" ("I chose these because...").
- **State Update:** `ui_state={...}` (Final cards)

---

## 5. Implementation Plan

1.  **State:** Define `AgentState` in `state.py` (DONE).
2.  **Tools:** Refactor `search_tool.py` to be stateless (pure functions).
3.  **Nodes:** Implement each node in `nodes/` folder.
    *   `playlist_analyzer.py`
    *   `track_finder.py` (Search + Enrich + Filter)
    *   `knowledge_processor.py` (Check + Process)
    *   `presenter.py`
4.  **Graph:** Wire it up in `graph.py` with conditional edges.
5.  **Test:** Verify with `manual_agent_test.py`.
