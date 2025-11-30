# Music Curator Agent v3 - Documentation

**Version:** 3.0 (Supervisor Pattern)  
**Last Updated:** 2025-11-30  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Agent Flow](#agent-flow)
4. [State Management](#state-management)
5. [Supervisor Decision Making](#supervisor-decision-making)
6. [API Endpoints](#api-endpoints)
7. [Frontend Integration](#frontend-integration)
8. [Error Handling](#error-handling)
9. [Testing](#testing)

---

## Overview

The Music Curator Agent v3 is a truly agentic system that uses a supervisor pattern to make intelligent decisions about how to curate personalized playlists. Unlike v2's deterministic state machine, v3 uses an LLM-powered supervisor that evaluates state and decides the next action autonomously.

### Key Features

- **Autonomous Decision Making**: Supervisor uses LLM to reason about next steps
- **Adaptive Search Strategy**: Automatically adjusts constraints based on results
- **Loop Prevention**: Detects and breaks out of infinite loops
- **Minimal User Interruption**: Only 2 questions maximum (vibe + artist knowledge)
- **Graceful Failure Handling**: Handles errors and edge cases intelligently
- **Transparent Reasoning**: Logs supervisor's decision-making process

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agent v3                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  START → SUPERVISOR (decision loop)                     │
│             ↓                                            │
│         [Decides next tool]                              │
│             ↓                                            │
│    ┌────────┴────────┐                                  │
│    ↓                 ↓                                   │
│  TOOLS          USER INTERRUPTS                          │
│  - analyze      - analyze (vibe Q)                       │
│  - search       - check_knowledge (artist Q)             │
│  - evaluate                                              │
│  - present                                               │
│    ↓                 ↓                                   │
│    └────────┬────────┘                                  │
│             ↓                                            │
│       SUPERVISOR (loop)                                  │
│             ↓                                            │
│         [mission complete?]                              │
│             ↓                                            │
│           END                                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **Supervisor Node**: The brain - analyzes state and decides next action
2. **Tool Nodes**: 5 discrete tools the supervisor can call
3. **State**: Complete agent state with flow control and data
4. **Graph**: LangGraph structure with interrupts and routing

---

## Agent Flow

### Typical Execution Path

```
1. START
   ↓
2. SUPERVISOR → decides "analyze_playlist"
   ↓
3. ANALYZE_PLAYLIST → generates vibe options
   ↓ (INTERRUPT - waits for user)
4. User selects vibe
   ↓
5. SUPERVISOR → decides "search_tracks"
   ↓
6. SEARCH_TRACKS → finds 50 candidates
   ↓
7. SUPERVISOR → decides "evaluate_results"
   ↓
8. EVALUATE_RESULTS → quality score 0.8 (good!)
   ↓
9. SUPERVISOR → decides "check_knowledge"
   ↓
10. CHECK_KNOWLEDGE → asks about artists
    ↓ (INTERRUPT - waits for user)
11. User selects known artists
    ↓
12. SUPERVISOR → decides "present_results"
    ↓
13. PRESENT_RESULTS → shows 5 tracks
    ↓
14. END
```

### Edge Case: User Knows All Artists

```
... (steps 1-11 same as above)
11. User selects "All of them"
    ↓
12. SUPERVISOR → decides "search_tracks" (with exclusions)
    ↓
13. SEARCH_TRACKS → finds new candidates (excluding known artists)
    ↓
14. SUPERVISOR → decides "present_results" (skip 2nd knowledge check)
    ↓
15. PRESENT_RESULTS → shows 5 tracks
    ↓
16. END
```

### Edge Case: Poor Quality Results

```
... (steps 1-6 same as above)
7. SUPERVISOR → decides "evaluate_results"
   ↓
8. EVALUATE_RESULTS → quality score 0.4 (poor!)
   ↓
9. SUPERVISOR → decides "search_tracks" (retry with relaxed constraints)
   ↓
10. SEARCH_TRACKS → finds more candidates
    ↓
11. SUPERVISOR → decides "evaluate_results"
    ↓
12. EVALUATE_RESULTS → quality score 0.7 (good!)
    ↓
13. SUPERVISOR → decides "check_knowledge"
    ... (continues normally)
```

---

## State Management

### AgentState Structure

```python
class AgentState(TypedDict):
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
    playlist_profile: Optional[Dict[str, Any]]
    candidate_tracks: List[Track]
    quality_assessment: Optional[Dict[str, Any]]
    known_artists: List[str]
    
    # --- Supervisor Control ---
    next_action: str  # Tool name or "END"
    supervisor_reasoning: str
    tool_parameters: Dict[str, Any]
    action_history: List[str]  # Last 3 actions for loop detection
    iteration_count: int
    
    # --- UI State ---
    ui_state: Optional[Dict[str, Any]]
    
    # --- Error Handling ---
    error: Optional[str]
```

### Track Structure

```python
class Track(TypedDict):
    id: str
    title: str
    artist: str
    album: Optional[str]
    uri: str
    distance: float  # Similarity score
    bpm: Optional[float]
    energy: Optional[float]
    danceability: Optional[float]
    valence: Optional[float]
    genres: List[str]
    reason: Optional[str]  # LLM-generated pitch
```

---

## Supervisor Decision Making

### How the Supervisor Works

The supervisor is an LLM-powered node that:

1. Receives current AgentState
2. Builds a context prompt with state information
3. Calls LLM with structured output (SupervisorDecision)
4. Returns next_action, reasoning, and parameters

### Decision Rules

The supervisor follows these rules (encoded in the prompt):

```
- If playlist not analyzed → MUST call analyze_playlist
- If vibe selected but no candidates → MUST call search_tracks
- If candidates exist but not evaluated → SHOULD call evaluate_results
- If quality poor and search_iter < 3 → CAN call search_tracks again
- If quality good and knowledge not checked → MUST call check_knowledge
- If knowledge checked and 5+ unknown tracks → MUST call present_results
- If user knows all and search_iter == 1 → MUST call search_tracks with exclusions
- If user knows all and search_iter > 1 → MUST call present_results
- If stuck or iteration >= 10 → MUST call present_results
```

### Loop Prevention

The supervisor has built-in loop prevention:

1. **Action History Tracking**: Keeps last 3 actions
2. **Loop Detection**: If same action 3x in a row, force different action
3. **Max Iterations**: If iteration_count >= 10, force present_results

### Example Supervisor Prompt

```
You are a music curator supervisor. Your mission: create a 5-track playlist of hidden gems.

Current State:
- Playlist analyzed: True
- Vibe selected: energy
- Search iteration: 1
- Candidates found: 50
- Quality score: 0.8
- Quality sufficient: True
- Knowledge checked: False
- Known artists: 0 ()
- Iteration: 3/10

Available Tools:
1. analyze_playlist - Analyze source playlist, ask user for vibe (INTERRUPTS USER)
2. search_tracks - Search for similar tracks with constraints
3. evaluate_results - Assess quality/quantity of current candidates
4. check_knowledge - Ask which artists user knows (INTERRUPTS USER)
5. present_results - Show final 5-track playlist (ENDS MISSION)

Decision Rules:
- You can only interrupt user TWICE total (analyze + check_knowledge)
- If playlist not analyzed → MUST call analyze_playlist
- If vibe selected but no candidates → MUST call search_tracks
- If candidates exist but not evaluated → SHOULD call evaluate_results
- If quality poor and search_iter < 3 → CAN call search_tracks again
- If quality good and knowledge not checked → MUST call check_knowledge
- If knowledge checked and 5+ unknown tracks → MUST call present_results
- If user knows all and search_iter == 1 → MUST call search_tracks with exclusions
- If user knows all and search_iter > 1 → MUST call present_results (give up gracefully)
- If stuck or iteration >= 10 → MUST call present_results

What should you do next?
```

**Supervisor Response:**
```json
{
  "next_action": "check_knowledge",
  "reasoning": "Quality is good (0.8) and we have 50 candidates. Knowledge hasn't been checked yet, so I should ask which artists the user knows.",
  "parameters": {}
}
```

---

## API Endpoints

### 1. Start Recommendation

**Endpoint:** `POST /agent/recommend/{playlist_id}`

**Description:** Starts the Music Curator Agent v3 for a playlist.

**Request:**
```http
POST /agent/recommend/123
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "I analyzed your playlist.\n\n📊 BPM: 120, Energy: 0.70\n\n💭 Upbeat indie rock with energetic vibes\n\nWhat vibe should I explore?",
  "options": [
    {"label": "🔥 More of this", "value": "similar"},
    {"label": "😌 Chill", "value": "chill"},
    {"label": "⚡ Energy", "value": "energy"},
    {"label": "🌟 Surprise", "value": "surprise"}
  ],
  "cards": []
}
```

---

### 2. Resume Agent

**Endpoint:** `POST /agent/resume`

**Description:** Resumes the agent with a user action.

**Request:**
```json
{
  "action": "set_vibe" | "submit_knowledge" | "add",
  "playlist_id": 123,
  "payload": {
    // Action-specific payload
  }
}
```

#### Action: `set_vibe`

User selected a vibe after analyze_playlist.

**Payload:**
```json
{
  "vibe": "similar" | "chill" | "energy" | "surprise"
}
```

#### Action: `submit_knowledge`

User selected known artists after check_knowledge.

**Payload:**
```json
{
  "known_artists": ["Artist A", "Artist B"]
}
```

**Special Values:**
- `["none"]`: User knows none of the artists → `known_artists = []`
- `["all"]`: User knows all artists → Supervisor will re-search with exclusions

#### Action: `add`

User wants to add a track to their playlist.

**Payload:**
```json
{
  "track_id": "track_123"
}
```

**Response:** `null` (no state change)

---

## Frontend Integration

### Starting the Agent

```typescript
const response = await fetch(`/agent/recommend/${playlistId}`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const uiState = await response.json();
renderUIState(uiState);
```

### Handling Vibe Selection

```typescript
const response = await fetch('/agent/resume', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'set_vibe',
    playlist_id: playlistId,
    payload: { vibe: selectedVibe }
  })
});

const uiState = await response.json();
renderUIState(uiState);
```

### Handling Artist Knowledge

```typescript
const response = await fetch('/agent/resume', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'submit_knowledge',
    playlist_id: playlistId,
    payload: { known_artists: selectedArtists }
  })
});

const uiState = await response.json();
renderUIState(uiState);
```

### UI State Rendering

```typescript
function renderUIState(state: UIState) {
  // Render message
  document.getElementById('message').textContent = state.message;
  
  // Render options (if any)
  if (state.options && state.options.length > 0) {
    renderOptions(state.options);
  }
  
  // Render cards (if any)
  if (state.cards && state.cards.length > 0) {
    renderTrackCards(state.cards);
  }
}
```

---

## Error Handling

### Empty Playlist

**Scenario:** Playlist has < 5 tracks

**Response:**
```json
{
  "message": "Your playlist needs more tracks! It currently has 2 tracks, but I need at least 5 to understand your taste. Add some more songs and try again.",
  "options": [],
  "cards": []
}
```

### No Candidates Found

**Scenario:** Search returns 0 tracks

**Response:**
```json
{
  "message": "I couldn't find any tracks matching your criteria. This might mean:\n\n• Your database doesn't have enough tracks yet\n• The vibe constraints were too strict\n\nTry adding more tracks to your library or selecting a different vibe!",
  "options": [],
  "cards": []
}
```

### LLM Service Failure

**Scenario:** LLM API is down

**Response:**
```json
{
  "message": "Sorry, our AI service is currently unavailable. Please try again later.",
  "options": [],
  "cards": []
}
```

### Max Iterations Reached

**Scenario:** Supervisor hits 10 iterations (safety limit)

**Behavior:** Supervisor automatically calls present_results with whatever tracks are available

---

## Testing

### Unit Tests

**Supervisor Tests** (`tests/test_supervisor_v3.py`):
- Initial state decision
- Max iterations enforcement
- Loop detection
- LLM failure handling
- Action history tracking

**Tool Tests** (`tests/test_tools_v3.py`):
- Evaluate results (sufficient/insufficient)
- Check knowledge (artist extraction)
- Present results (prioritize unknown artists)
- Present results (no candidates)

### Integration Tests

**Graph Tests** (`tests/test_integration_v3.py`):
- Graph compiles successfully
- All nodes present
- Interrupts configured correctly

### Running Tests

```bash
# Run all v3 tests
pytest tests/test_supervisor_v3.py tests/test_tools_v3.py tests/test_integration_v3.py -v

# Run with coverage
pytest tests/test_*_v3.py --cov=api/agents/gem_hunter/nodes --cov-report=html
```

---

## Configuration

### Environment Variables

```bash
# LLM Models
LLM_CREATIVE_MODEL=claude-3-5-haiku-20241022  # For pitches
LLM_REASONING_MODEL=claude-sonnet-4-5-20250929  # For supervisor

# Database
DATABASE_URL=postgresql://...

# API Keys
ANTHROPIC_API_KEY=...
```

---

## Comparison: v2 vs v3

| Feature | v2 (State Machine) | v3 (Supervisor) |
|---------|-------------------|-----------------|
| Decision Making | Hardcoded flow | LLM-powered |
| Adaptability | Fixed path | Dynamic |
| Loop Prevention | Manual checks | Automatic |
| Error Recovery | Predefined | Intelligent |
| Transparency | Limited | Full reasoning |
| Complexity | Simple | Moderate |
| Reliability | High | High |

---

## Changelog

### Version 3.0 (2025-11-30)
- Introduced supervisor pattern
- LLM-powered decision making
- Automatic loop prevention
- Adaptive search strategy
- Improved error handling
- Added comprehensive testing

---

## Support

For issues or questions, contact the development team or file an issue in the repository.


---

## Troubleshooting

### Common Issues

#### 1. Validation Error: embedding_512_vector

**Error:**
```
ValidationError: 1 validation error for Track
embedding_512_vector
  Input should be a valid list [type=list_type, input_value='[3.28...', input_type=str]
```

**Cause:** Database returns embedding as string instead of list (PostgreSQL pgvector issue)

**Fix:** Use the existing codec in `api/core/db_codecs.py`:
```python
# In api/repositories/library.py
from api.core.db_codecs import decode_vector

# When fetching tracks:
for row in rows:
    track_dict = dict(row)
    if 'embedding_512_vector' in track_dict:
        track_dict['embedding_512_vector'] = decode_vector(track_dict['embedding_512_vector'])
    tracks.append(Track(**track_dict))
```

Or register the codec globally when creating the connection pool.

**Agent Behavior:** The v3 agent handles this gracefully:
- Detects the loop (search_tracks fails 3x)
- Forces present_results with error message
- User sees: "I encountered an issue: [error]. Please try again or adjust your preferences."

#### 2. Agent Loops Infinitely

**Symptom:** Same action called repeatedly

**v3 Solution:** Automatic loop detection
```
⚠️ Loop detected: ['search_tracks', 'search_tracks', 'search_tracks']. Forcing different action.
```

The supervisor automatically breaks the loop after 3 identical actions.

#### 3. Max Iterations Reached

**Symptom:** Agent stops after 10 iterations

**Cause:** Safety limit to prevent infinite execution

**Solution:** This is expected behavior. The agent will present whatever results it has.

#### 4. No Candidates Found

**Symptom:** Search returns 0 tracks

**Possible Causes:**
- Database has insufficient tracks
- Vibe constraints too strict
- All tracks excluded (known artists)

**Agent Behavior:**
- Tries up to 3 times with relaxed constraints
- If still no results, presents error message

#### 5. LLM Service Unavailable

**Symptom:** Supervisor or tool fails with LLM error

**Agent Behavior:**
- Catches exception
- Forces present_results
- Returns user-friendly error message

---

## Performance Monitoring

### Key Metrics to Track

1. **Iteration Count**: Should be < 10 (typically 4-6)
2. **Search Iterations**: Should be 1-2 (3 indicates issues)
3. **Loop Detection**: Should be rare (indicates data/config issues)
4. **LLM Calls**: ~2-4 per session (supervisor + pitches)
5. **Response Time**: ~5-10 seconds total

### Logging

The agent logs all decisions:
```
🧠 Supervisor thinking...
✅ Decision: search_tracks
   Reasoning: Vibe selected but no candidates, must search
```

Monitor these logs to understand agent behavior.

---

## Known Limitations

1. **Max 2 User Interrupts**: By design (vibe + artist knowledge)
2. **Max 10 Iterations**: Safety limit to prevent infinite loops
3. **Max 3 Search Attempts**: Prevents excessive database queries
4. **Embedding Format**: Requires list, not string (see troubleshooting)

---
