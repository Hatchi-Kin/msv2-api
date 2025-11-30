# Hidden Gem Hunter Agent - Current Architecture

**Last Updated:** 2025-11-29  
**Status:** ✅ Supervisor Pattern Implemented  
**Branch:** `new_agent`

---

## 🏗️ Architecture Overview

The agent uses a **Supervisor Pattern** where an LLM-powered supervisor dynamically decides which tools to call based on the current state.

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agent                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌─────────────────────────┐  │
│  │  Supervisor  │────────▶│   Tool Nodes            │  │
│  │    Node      │         │  - search_tracks        │  │
│  │  (LLM Brain) │         │  - filter_by_audio      │  │
│  └──────────────┘         │  - enrich_tracks        │  │
│         │                 │  - check_knowledge      │  │
│         │                 │  - ask_user             │  │
│         ▼                 └─────────────────────────┘  │
│  ┌──────────────┐                     │                │
│  │ Presentation │◀────────────────────┘                │
│  │    Node      │                                      │
│  └──────────────┘                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
api/agents/gem_hunter/
├── graph.py                          # LangGraph definition
├── state.py                          # AgentState & UIState models
├── llm_factory.py                    # LLM initialization
│
├── nodes/
│   ├── supervisor_node.py            # Brain: decides next action
│   ├── tool_nodes.py                 # Worker nodes (search, filter, etc.)
│   ├── presentation_node_v2.py       # Final presentation logic
│   └── [legacy nodes - deprecated]
│
├── tools/
│   └── search_tool.py                # DB search & filtering functions
│
├── llm/
│   ├── pitch_writer.py               # Generate track pitches
│   └── justification_generator.py    # Generate final explanations
│
└── core/
    ├── metadata_enrichment.py        # Spotify enrichment (legacy)
    └── track_formatting.py           # Format tracks for UI
```

---

## 🧠 Supervisor Node

**File:** `nodes/supervisor_node.py`

### Purpose
The supervisor is the "brain" of the agent. It:
1. Analyzes the current state
2. Decides the next action using an LLM
3. Updates the thought process for UI streaming

### Decision Logic

```python
class SupervisorDecision(BaseModel):
    next_action: Literal[
        "search_tracks",
        "filter_by_audio",
        "enrich_tracks",
        "check_artist_knowledge",
        "present_results",
        "ask_user"
    ]
    reasoning: str
    parameters: Dict[str, Any]
```

### Context Provided to LLM

- User preferences (e.g., "upbeat music")
- Playlist profile (avg BPM, energy, genres)
- Current candidates count
- Enriched tracks count
- Known artists (to exclude)
- Current constraints (BPM, energy filters)
- Iteration count (to prevent infinite loops)

### Safety Features

- **Max iterations:** 25 (prevents infinite loops)
- **Fallback:** If LLM fails, defaults to `present_results`

---

## 🛠️ Tool Nodes

**File:** `nodes/tool_nodes.py`

### 1. `search_tracks`
**Purpose:** Find similar tracks using vector similarity search

**Logic:**
1. Get or calculate playlist centroid (512-dim vector)
2. Search for similar tracks in `megaset` table
3. Exclude known artists and already-seen tracks
4. Apply optional constraints (BPM, energy, etc.)

**Returns:** List of candidate tracks

---

### 2. `filter_by_audio`
**Purpose:** Filter tracks by audio features (BPM, energy, harmonic ratio)

**Logic:**
1. Takes `enriched_tracks` (not `candidate_tracks`)
2. Applies filters based on parameters
3. **Lenient mode:** Keeps tracks with missing audio features (for when batch extraction is incomplete)

**Returns:** Filtered list of tracks

**Note:** Currently lenient because audio feature extraction is ongoing.

---

### 3. `enrich_tracks`
**Purpose:** Promote candidates to enriched status

**Logic:**
- In the new architecture, tracks from DB already have audio features
- This tool simply promotes `candidate_tracks` → `enriched_tracks`
- In the future, could fetch Spotify images/preview URLs here

**Returns:** Enriched tracks

---

### 4. `check_knowledge`
**Purpose:** Ask user which artists they know

**Logic:**
1. Extract unique artists from candidates
2. Create UI options for user to select known artists
3. Pause execution (returns to END)

**Returns:** UI state with artist selection options

**Note:** Currently basic. Will be enhanced to use reference tracks.

---

### 5. `ask_user`
**Purpose:** Ask clarifying questions

**Logic:**
1. Supervisor provides question + options
2. Creates UI state with buttons
3. Pauses execution

**Returns:** UI state with question and options

---

## 🎨 Presentation Node

**File:** `nodes/presentation_node_v2.py`

### Purpose
Generate final recommendations with LLM-powered explanations

### Steps
1. **Generate Pitches:** Create compelling 1-sentence descriptions for each track
2. **Generate Justification:** Explain why these tracks were chosen
3. **Create Track Cards:** Format tracks for UI display
4. **Return UI State:** Complete message with cards

### Output Structure

```python
UIState(
    message="Combined understanding + selection",
    understanding="Why I chose these based on your playlist...",
    selection="How these tracks match your vibe...",
    cards=[TrackCard, ...],
    options=[],
    thought_process=["Decision: ...", "Decision: ..."]
)
```

---

## 📊 State Management

**File:** `state.py`

### AgentState (TypedDict)

```python
{
    # Core
    "playlist_id": int,
    "user_preferences": str,
    
    # Working Memory
    "centroid": List[float],              # 512-dim vector
    "candidate_tracks": List[dict],       # Raw search results
    "enriched_tracks": List[dict],        # Promoted candidates
    "playlist_profile": Dict,             # Stats (avg BPM, energy, genres)
    "constraints": Dict,                  # Current filters
    
    # Supervisor Control
    "next_action": str,                   # Next tool to call
    "supervisor_reasoning": str,          # Why this action
    "tool_parameters": Dict,              # Parameters for tool
    "_iteration_count": int,              # Safety counter
    
    # User Interaction
    "excluded_ids": List[int],            # Tracks to skip
    "excluded_artists": List[str],        # Artists to exclude
    "known_artists": List[str],           # Artists user knows
    
    # UI Output
    "ui_state": dict,                     # Current UI state
    
    # Legacy (to be removed)
    "next_step": str,
    "knowledge_checked": bool,
    "vibe_checked": bool,
}
```

### UIState (Pydantic)

```python
class UIState(BaseModel):
    message: str                          # Main message to user
    understanding: Optional[str]          # Why these tracks (Part 1)
    selection: Optional[str]              # How they match (Part 2)
    cards: List[TrackCard]                # Track recommendations
    options: List[ButtonOption]           # Click-only options
    thought_process: Optional[List[str]]  # Agent's reasoning (for streaming)
```

### TrackCard

```python
class TrackCard(BaseModel):
    id: int
    title: str
    artist: str
    album: Optional[str]
    reason: str                           # LLM-generated pitch
    
    # Audio Features (NEW)
    bpm: Optional[float]
    energy: Optional[float]
    brightness: Optional[float]
    harmonic_ratio: Optional[float]
```

---

## 🔄 Graph Flow

**File:** `graph.py`

### Graph Structure

```
START
  ↓
supervisor ←──────────────┐
  ↓                        │
  ├─→ search_tracks ──────┤
  ├─→ filter_by_audio ────┤
  ├─→ enrich_tracks ──────┤
  ├─→ check_knowledge ────→ END (wait for user)
  ├─→ ask_user ───────────→ END (wait for user)
  └─→ present_results ────→ END
```

### Routing Logic

```python
def route_supervisor(state: AgentState):
    action = state.get("next_action")
    
    if action == "search_tracks":
        return "search_tracks"
    elif action == "filter_by_audio":
        return "filter_by_audio"
    # ... etc
    else:
        return END
```

### Checkpointing

- **Type:** PostgreSQL (`AsyncPostgresSaver`)
- **Connection:** Uses `from_conn_string()` with DATABASE_URL
- **Thread ID:** `f"playlist_{playlist_id}"`
- **Tables:** Auto-created by `checkpointer.setup()`

**Benefits:**
- State persists across server restarts
- Can resume conversations
- Scales to multiple API instances

---

## 🗄️ Database Integration

### Tables Used

#### `megaset`
Main track table with audio features:

```sql
- id, title, artist, album, year, genre
- embedding_512_vector (pgvector)
- bpm, energy, brightness, harmonic_ratio
- onset_strength, dynamic_range, estimated_key
- mfcc_vector (JSONB)
```

#### `checkpoints` (LangGraph)
Auto-created by `AsyncPostgresSaver`:
- Stores agent state between interactions
- Enables conversation resumption

### Key Queries

**1. Vector Similarity Search**
```python
# In search_tool.py::search_similar_tracks()
await repo.search_hidden_gems_with_filters(
    centroid=centroid,
    exclude_ids=[...],
    exclude_artists=[...],
    min_bpm=120,
    max_bpm=140,
    min_energy=0.6,
    limit=10
)
```

**2. Playlist Centroid**
```python
# In LibraryRepository
centroid = await repo.get_playlist_centroid(playlist_id)
# Returns average of all track embeddings in playlist
```

---

## 🎯 Current Limitations

### 1. Audio Features Incomplete
- **Issue:** Batch extraction still running
- **Impact:** `filter_by_audio` keeps all tracks (lenient mode)
- **Solution:** Wait for batch script to complete

### 2. No Playlist Analysis
- **Issue:** Supervisor doesn't analyze playlist vibe yet
- **Impact:** Can't show "I analyzed your playlist..." message
- **Solution:** Implement `analyze_playlist_vibe` tool (next phase)

### 3. Basic Artist Knowledge Check
- **Issue:** Just asks "Do you know these artists?"
- **Impact:** Doesn't use reference tracks from known artists
- **Solution:** Enhance with smart reference questions (next phase)

### 4. No Save Playlist Action
- **Issue:** User can't save results as a new playlist
- **Impact:** Recommendations are ephemeral
- **Solution:** Add `save_playlist` action (next phase)

---

## 🚀 Next Steps (See ENHANCED_FLOW_PROPOSAL.md)

1. **Playlist Analysis Tool** - Generate natural language vibe description
2. **Smart Artist Knowledge** - Use reference tracks from known artists
3. **Save Playlist Action** - Allow user to save recommendations
4. **Streaming UI** - Show `thought_process` in real-time

---

## 🧪 Testing

### Manual Test Script
```bash
python tests/manual_agent_test.py
```

**Features:**
- Uses Postgres checkpointer (persistence)
- Shows thought process
- Interactive CLI for testing flows

### Current Test Flow
1. Select playlist ID
2. Enter preferences (e.g., "upbeat")
3. Agent searches → enriches → filters → loops (if no audio features)
4. Hits max iterations (25) and presents what it has

---

## 📝 Configuration

### Environment Variables

```bash
# LLM Models
LLM_REASONING_MODEL=claude-sonnet-4-5-20250929  # Supervisor decisions
LLM_CREATIVE_MODEL=claude-3-5-haiku-20241022    # Pitches & justifications

# Database
DATABASE_URL=postgresql://...

# API Keys
ANTHROPIC_API_KEY=...
```

### LLM Usage

- **Supervisor:** Uses `LLM_REASONING_MODEL` (temp=0) for consistent decisions
- **Pitches:** Uses `LLM_CREATIVE_MODEL` (temp=0.7) for variety
- **Justifications:** Uses `LLM_REASONING_MODEL` (temp=0) for clarity

---

## 🐛 Known Issues

### 1. Infinite Loop (FIXED)
- **Symptom:** Agent keeps calling `search_tracks` → `filter_by_audio` → `search_tracks`
- **Cause:** Filter returns 0 tracks (no audio features in DB)
- **Fix:** Made filter lenient + added max iteration limit

### 2. Enrichment Does Nothing
- **Symptom:** `enrich_tracks` just copies candidates
- **Cause:** DB already has audio features, no Spotify call needed
- **Status:** Working as intended for now

### 3. Checkpointer Type Error (FIXED)
- **Symptom:** `TypeError: Invalid connection type: <class 'asyncpg.pool.Pool'>`
- **Cause:** `AsyncPostgresSaver` expects `psycopg` pool, not `asyncpg`
- **Fix:** Use `AsyncPostgresSaver.from_conn_string()` instead

---

## 📚 Related Documentation

- `ENHANCED_FLOW_PROPOSAL.md` - Next phase design
- `AUDIO_FEATURES_GUIDE.md` - Audio feature extraction details
- `IMPLEMENTATION_ROADMAP.md` - Original roadmap (outdated)
- `PROPOSAL_SUPERVISOR_AGENT.md` - Original supervisor design
