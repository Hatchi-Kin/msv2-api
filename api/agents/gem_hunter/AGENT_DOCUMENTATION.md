# Music Curator Agent - Complete Documentation

**Version:** 3.0 (Supervisor Pattern)  
**Last Updated:** 2025-11-30  
**Status:** ✅ Production Ready

> **Note:** This is version 3.0 which uses a supervisor pattern for autonomous decision-making. For v2 documentation (state machine), see `AGENT_DOCUMENTATION_V2.md`.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Agent Flow](#agent-flow)
3. [State Management](#state-management)
4. [API Endpoints](#api-endpoints)
5. [UI State Structure](#ui-state-structure)
6. [Frontend Integration Guide](#frontend-integration-guide)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

---

## Overview

The Music Curator Agent is a truly agentic LangGraph system that autonomously curates personalized playlists. Unlike traditional state machines, it uses an LLM-powered supervisor to make intelligent decisions about search strategy, quality evaluation, and when to present results.

### Key Features

- **Autonomous Decision Making**: Supervisor uses LLM to reason about next steps
- **Adaptive Search Strategy**: Automatically adjusts constraints based on results quality
- **Loop Prevention**: Detects and breaks out of infinite loops automatically
- **Minimal User Interruption**: Only 2 questions maximum (vibe + artist knowledge)
- **Graceful Failure Handling**: Handles errors and edge cases intelligently
- **Transparent Reasoning**: Logs supervisor's decision-making process
- **LLM-Powered Pitches**: Generates compelling descriptions for each recommended track

### Architecture

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

---

## Agent Flow

### Typical Execution Path

The supervisor makes decisions at each step based on the current state:

#### 1. **Start** (`POST /agent/recommend/{playlist_id}`)
- Frontend calls the API with a playlist ID
- Agent initializes with default state
- Supervisor evaluates state

#### 2. **Supervisor Decision: analyze_playlist**
- Supervisor sees playlist not analyzed
- Decides to call `analyze_playlist` tool

#### 3. **Analyze Playlist Tool**
- Fetches playlist statistics (avg BPM, top genres, track count)
- Validates playlist has at least 5 tracks
- Generates natural language description using LLM
- Creates 4 vibe options for user to choose from
- **INTERRUPTS** - Returns UI state with options
- Waits for user to select a vibe

**UI State Returned:**
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

#### 4. **User Selects Vibe** (`POST /agent/resume`)
- Frontend sends selected vibe via resume endpoint
- Agent updates state with `vibe_choice`
- Supervisor evaluates state again

**Request:**
```json
{
  "action": "set_vibe",
  "playlist_id": 123,
  "payload": {"vibe": "energy"}
}
```

#### 5. **Supervisor Decision: search_tracks**
- Supervisor sees vibe selected but no candidates
- Decides to call `search_tracks` tool

#### 6. **Search Tracks Tool**
- Calculates playlist centroid (average embedding vector)
- Applies constraints based on vibe choice:
  - `chill`: max_energy=0.6, max_bpm=110
  - `energy`: min_energy=0.7, min_bpm=120
  - `similar`: min_bpm=avg-20, max_bpm=avg+20
  - `surprise`: no constraints
- Searches for 50 similar tracks using vector similarity
- Excludes artists from `known_artists` list
- Returns to supervisor

#### 7. **Supervisor Decision: evaluate_results**
- Supervisor sees candidates exist but not evaluated
- Decides to call `evaluate_results` tool

#### 8. **Evaluate Results Tool**
- Calculates quantity score (candidates / 50)
- Calculates quality score (1 - avg_distance)
- Calculates diversity score (unique_artists / 20)
- Computes overall score
- Returns assessment to supervisor

#### 9. **Supervisor Decision: check_knowledge**
- Supervisor sees quality is good and knowledge not checked
- Decides to call `check_knowledge` tool

#### 10. **Check Knowledge Tool**
- Extracts unique artists from top 20 candidates
- Creates UI options for user to select known artists
- **INTERRUPTS** - Returns UI state with artist options
- Waits for user to select known artists

**UI State Returned:**
```json
{
  "message": "Which of these artists do you know? (Select all that apply)",
  "options": [
    {"label": "Artist A", "value": "Artist A"},
    {"label": "Artist B", "value": "Artist B"},
    {"label": "Artist C", "value": "Artist C"},
    {"label": "None of them", "value": "none"},
    {"label": "All of them", "value": "all"}
  ],
  "cards": []
}
```

#### 11. **User Selects Known Artists** (`POST /agent/resume`)
- Frontend sends list of known artists
- Agent updates state with `known_artists`
- Supervisor evaluates state again

**Request:**
```json
{
  "action": "submit_knowledge",
  "playlist_id": 123,
  "payload": {"known_artists": ["Artist A", "Artist C"]}
}
```

**Special Values:**
- `["none"]`: Converted to empty array `[]`
- `["all"]`: Converted to list of all candidate artists

#### 12. **Supervisor Decision: present_results**
- Supervisor sees knowledge checked and has 5+ unknown tracks
- Decides to call `present_results` tool

**Alternative Flow (User Knows All):**
- If user selects "all", supervisor sees all artists are known
- On first occurrence: Decides to call `search_tracks` again with exclusions
- On second occurrence: Decides to call `present_results` (give up gracefully)

#### 13. **Present Results Tool**
- Filters candidates to prioritize unknown artists
- Selects top 5 tracks (unknown first, then known if needed)
- Generates LLM-powered pitch for each track
- Generates overall justification
- Returns final UI state with track cards
- **END** - Agent execution complete

**UI State Returned:**
```json
{
  "message": "Here are some hidden gems I found for you!",
  "options": [
    {"label": "Save Playlist", "value": "save"}
  ],
  "cards": [
    {
      "id": "track_123",
      "title": "Song Title",
      "artist": "Artist Name",
      "reason": "A dreamy indie track with shimmering guitars and ethereal vocals that perfectly captures the vibe you're looking for."
    }
  ],
  "thought_process": []
}
```

---

## State Management

### AgentState Structure

```python
class AgentState(TypedDict):
    # --- Input ---
    playlist_id: str              # ID of the playlist to analyze
    user_id: str                  # ID of the user
    
    # --- Flow Control Flags ---
    playlist_analyzed: bool       # Has playlist been analyzed?
    vibe_choice: Optional[str]    # "similar" | "chill" | "energy" | "surprise"
    search_iteration: int         # Number of search attempts (for adaptive strategy)
    knowledge_checked: bool       # Has artist knowledge been checked?
    results_presented: bool       # Have results been presented?
    
    # --- Data State ---
    playlist_profile: Optional[Dict[str, Any]]  # {avg_bpm, avg_energy, top_genres, description}
    candidate_tracks: List[Track]               # Search results
    quality_assessment: Optional[Dict[str, Any]] # {sufficient, quality_score, recommendation}
    known_artists: List[str]                    # Artists user knows
    
    # --- Supervisor Control ---
    next_action: str              # Tool name or "END"
    supervisor_reasoning: str     # Why supervisor chose this action
    tool_parameters: Dict[str, Any]  # Parameters for next tool
    action_history: List[str]     # Last 3 actions for loop detection
    iteration_count: int          # Safety counter (max 10)
    
    # --- UI State ---
    ui_state: Optional[Dict[str, Any]]  # Current UI state to render
    
    # --- Error Handling ---
    error: Optional[str]          # Error message if any
```

### Track Structure

```python
class Track(TypedDict):
    id: str                       # Track ID
    title: str                    # Track title
    artist: str                   # Artist name
    album: Optional[str]          # Album name
    uri: str                      # Spotify URI or file path
    distance: float               # Similarity score from vector search
    bpm: Optional[float]          # Beats per minute
    energy: Optional[float]       # Energy level (0-1)
    danceability: Optional[float] # Danceability (0-1)
    valence: Optional[float]      # Valence/mood (0-1)
    genres: List[str]             # List of genres
    reason: Optional[str]         # Why this track was chosen (LLM-generated)
```

### UIState Structure

```python
class UIState(TypedDict):
    message: str                  # Main message to display
    options: List[Dict]           # List of button options
    cards: List[Dict]             # List of track cards (if presenting results)
```

**Option Structure:**
```python
{
    "label": str,    # Button text (e.g., "🔥 More of this")
    "value": str     # Value to send back (e.g., "similar")
}
```

**Card Structure:**
```python
{
    "id": str,       # Track ID
    "title": str,    # Track title
    "artist": str,   # Artist name
    "reason": str    # LLM-generated pitch
}
```

---

## Supervisor Decision Making

### How the Supervisor Works

The supervisor is the "brain" of the agent. After each tool execution, the supervisor:

1. **Analyzes Current State**: Examines all state fields (flags, data, history)
2. **Builds Context**: Creates a detailed prompt with state information and decision rules
3. **Calls LLM**: Uses structured output to get next_action, reasoning, and parameters
4. **Updates State**: Records decision and increments counters
5. **Routes Execution**: Graph routes to the chosen tool or END

### Decision Rules

The supervisor follows these rules (encoded in its prompt):

```
- If playlist not analyzed → MUST call analyze_playlist
- If vibe selected but no candidates → MUST call search_tracks
- If candidates exist but not evaluated → SHOULD call evaluate_results
- If quality poor and search_iter < 3 → CAN call search_tracks again
- If quality good and knowledge not checked → MUST call check_knowledge
- If knowledge checked and 5+ unknown tracks → MUST call present_results
- If user knows all and search_iter == 1 → MUST call search_tracks with exclusions
- If user knows all and search_iter > 1 → MUST call present_results (give up gracefully)
- If stuck or iteration >= 10 → MUST call present_results
```

### Loop Prevention

The supervisor has built-in safety mechanisms:

1. **Action History**: Tracks last 3 actions
2. **Loop Detection**: If same action 3x in a row → force present_results
3. **Max Iterations**: If iteration_count >= 10 → force present_results

### Example Supervisor Decision

**State:**
```
- Playlist analyzed: True
- Vibe selected: energy
- Candidates found: 50
- Quality score: 0.8 (good!)
- Knowledge checked: False
- Iteration: 3/10
```

**Supervisor Decision:**
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

**Description:** Starts the Hidden Gem Hunter agent for a playlist.

**Request:**
```http
POST /agent/recommend/123
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "I analyzed your playlist...",
  "options": [...],
  "cards": [],
  "thought_process": []
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: Playlist not found
- `500 Internal Server Error`: Agent execution failed

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
  },
  "track_id": null  // Optional, for "add" action
}
```

**Actions:**

#### `set_vibe`
User selected a vibe direction.

**Payload:**
```json
{
  "vibe": "similar" | "chill" | "energy" | "surprise"
}
```

#### `submit_knowledge`
User selected known artists.

**Payload:**
```json
{
  "known_artists": ["Artist A", "Artist B"]
}
```

Special values:
- `["none"]`: User knows none of the artists
- `["all"]`: User knows all of the artists

#### `add`
User wants to add a track to their playlist.

**Payload:**
```json
{
  "track_id": "track_123"
}
```

**Response:**
- For `set_vibe` and `submit_knowledge`: Returns next UIState
- For `add`: Returns `null` (no state change, just DB update)

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Invalid or missing token
- `500 Internal Server Error`: Agent execution failed

---

## UI State Structure

The agent communicates with the frontend through the `UIState` object. Here's how to interpret each state:

### State 1: Vibe Selection

**Characteristics:**
- `message`: Contains playlist analysis
- `options`: 4 vibe choices
- `cards`: Empty array

**Frontend Action:**
- Display message
- Render 4 buttons from `options`
- On button click, call `/agent/resume` with `action: "set_vibe"`

**Example:**
```json
{
  "message": "I analyzed your playlist.\n\n📊 **Stats:**\n• BPM: 120\n• Genres: pop, rock\n\n💭 **Vibe:** Upbeat indie rock\n\nWhat direction should I explore?",
  "options": [
    {"label": "🔥 More of this (Similar Vibe)", "value": "similar"},
    {"label": "😌 Dial it down (Chill)", "value": "chill"},
    {"label": "⚡ Pump it up (High Energy)", "value": "energy"},
    {"label": "🌟 Surprise me", "value": "surprise"}
  ],
  "cards": [],
  "thought_process": []
}
```

---

### State 2: Artist Knowledge Check

**Characteristics:**
- `message`: "Do you know any of these artists?"
- `options`: List of artists + "None" + "All"
- `cards`: Empty array

**Frontend Action:**
- Display message
- Render checkboxes or multi-select from `options`
- Add "Submit" button
- On submit, call `/agent/resume` with `action: "submit_knowledge"`

**Example:**
```json
{
  "message": "Do you know any of these artists? Select the ones you know:",
  "options": [
    {"label": "Tame Impala", "value": "Tame Impala"},
    {"label": "MGMT", "value": "MGMT"},
    {"label": "Phoenix", "value": "Phoenix"},
    {"label": "None of them", "value": "none"},
    {"label": "All of them", "value": "all"}
  ],
  "cards": [],
  "thought_process": []
}
```

**Special Handling:**
- If user selects "None of them", send `known_artists: ["none"]`
- If user selects "All of them", send `known_artists: ["all"]`
- Otherwise, send array of selected artist names

---

### State 3: Results Presentation

**Characteristics:**
- `message`: "Here are some hidden gems..."
- `options`: ["Save Playlist"] or empty
- `cards`: Array of 5 track cards

**Frontend Action:**
- Display message
- Render track cards with:
  - Title
  - Artist
  - Reason (LLM-generated pitch)
  - Play button (if preview_url available)
  - Add button (calls `/agent/resume` with `action: "add"`)
- Optionally render "Save Playlist" button

**Example:**
```json
{
  "message": "Here are some hidden gems I found for you!",
  "options": [
    {"label": "Save Playlist", "value": "save"}
  ],
  "cards": [
    {
      "id": "track_123",
      "title": "Midnight City",
      "artist": "M83",
      "reason": "A soaring synth anthem with infectious energy and dreamy atmosphere that perfectly captures your upbeat indie vibe."
    },
    {
      "id": "track_456",
      "title": "Sleepyhead",
      "artist": "Passion Pit",
      "reason": "Frenetic electro-pop with cascading synths and falsetto vocals that will energize your playlist."
    }
  ],
  "thought_process": []
}
```

---

## Frontend Integration Guide

### 1. Initial Setup

```typescript
// Types
interface UIState {
  message: string;
  options: Array<{label: string; value: string}>;
  cards: Array<{id: string; title: string; artist: string; reason: string}>;
  thought_process: string[];
}

interface ResumeRequest {
  action: 'set_vibe' | 'submit_knowledge' | 'add';
  playlist_id: number;
  payload: Record<string, any>;
  track_id?: string;
}
```

### 2. Starting the Agent

```typescript
async function startAgent(playlistId: number): Promise<UIState> {
  const response = await fetch(`/agent/recommend/${playlistId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to start agent');
  }
  
  return await response.json();
}
```

### 3. Resuming the Agent

```typescript
async function resumeAgent(request: ResumeRequest): Promise<UIState | null> {
  const response = await fetch('/agent/resume', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });
  
  if (!response.ok) {
    throw new Error('Failed to resume agent');
  }
  
  // Note: Returns null for "add" action
  return await response.json();
}
```

### 4. Handling Vibe Selection

```typescript
async function handleVibeSelection(vibe: string, playlistId: number) {
  const uiState = await resumeAgent({
    action: 'set_vibe',
    playlist_id: playlistId,
    payload: { vibe }
  });
  
  // Update UI with new state
  renderUIState(uiState);
}
```

### 5. Handling Artist Knowledge

```typescript
async function handleKnowledgeSubmit(
  selectedArtists: string[], 
  playlistId: number
) {
  const uiState = await resumeAgent({
    action: 'submit_knowledge',
    playlist_id: playlistId,
    payload: { known_artists: selectedArtists }
  });
  
  // Update UI with new state
  renderUIState(uiState);
}
```

### 6. Adding a Track

```typescript
async function handleAddTrack(trackId: string, playlistId: number) {
  await resumeAgent({
    action: 'add',
    playlist_id: playlistId,
    payload: {},
    track_id: trackId
  });
  
  // Show success message (no state change)
  showToast('Track added to playlist!');
}
```

### 7. Rendering UI State

```typescript
function renderUIState(state: UIState) {
  // Render message
  document.getElementById('message').innerHTML = state.message;
  
  // Render options (buttons)
  if (state.options.length > 0 && state.cards.length === 0) {
    // This is a selection state (vibe or knowledge)
    renderOptions(state.options);
  }
  
  // Render cards (results)
  if (state.cards.length > 0) {
    renderTrackCards(state.cards);
  }
}
```

---

## Error Handling

### Common Errors

#### 1. LLM Service Unavailable

**Symptom:** Agent returns error message in UI state

**Response:**
```json
{
  "message": "Sorry, our AI service is currently unavailable. Please try again later.",
  "cards": [],
  "options": [],
  "thought_process": []
}
```

**Frontend Action:**
- Display error message
- Provide "Try Again" button
- Log error for monitoring

#### 2. No Tracks Found

**Symptom:** Agent completes but returns 0 cards

**Response:**
```json
{
  "message": "I couldn't find any hidden gems matching your criteria. Try a different vibe!",
  "cards": [],
  "options": [
    {"label": "Try Again", "value": "restart"}
  ],
  "thought_process": []
}
```

**Frontend Action:**
- Display message
- Provide option to restart with different vibe

#### 3. Playlist Has No Tracks

**Symptom:** 500 error on start

**Frontend Action:**
- Catch error
- Display: "This playlist is empty. Add some tracks first!"
- Provide link to playlist

#### 4. User Knows All Artists (Twice)

**Symptom:** Agent presents tracks even though user knows all artists

**Explanation:** This is expected behavior. After one re-search attempt, the agent will present whatever it has rather than loop infinitely.

**Frontend Action:**
- Display results normally
- Optionally show message: "These are the closest matches we could find, even though you know these artists."

---

## Examples

### Complete Flow Example

```typescript
// 1. User clicks "Find Hidden Gems" on a playlist
const playlistId = 123;

// 2. Start agent
const state1 = await startAgent(playlistId);
// Returns: Vibe selection UI

// 3. User selects "High Energy"
const state2 = await resumeAgent({
  action: 'set_vibe',
  playlist_id: playlistId,
  payload: { vibe: 'energy' }
});
// Agent searches, filters, returns: Artist knowledge check UI

// 4. User selects known artists
const state3 = await resumeAgent({
  action: 'submit_knowledge',
  playlist_id: playlistId,
  payload: { known_artists: ['Artist A', 'Artist B'] }
});
// Returns: Results presentation UI with 5 track cards

// 5. User adds a track
await resumeAgent({
  action: 'add',
  playlist_id: playlistId,
  payload: {},
  track_id: 'track_123'
});
// Returns: null (track added to DB)
```

### Edge Case: User Knows All Artists

```typescript
// 1-3. Same as above...

// 4. User selects "All of them"
const state3 = await resumeAgent({
  action: 'submit_knowledge',
  playlist_id: playlistId,
  payload: { known_artists: ['all'] }
});
// Agent automatically re-searches with excluded artists
// Returns: Results presentation UI with NEW tracks

// If user somehow knows all artists again, agent will present them anyway
```

---

## Technical Details

### Checkpointing

The agent uses LangGraph's checkpointing feature to persist state between API calls. Each playlist has its own thread:

```python
thread_id = f"playlist_{playlist_id}"
config = {"configurable": {"thread_id": thread_id}}
```

This allows:
- Resuming conversations after interrupts
- Multiple users using the agent simultaneously
- State persistence across server restarts (if using PostgreSQL checkpointer)

### Vector Search

The agent uses pgvector for similarity search:

1. Calculate playlist centroid (average of all track embeddings)
2. Search for tracks with similar embeddings
3. Exclude known artists
4. Apply audio feature constraints (BPM, energy)
5. Return top 50 candidates

### LLM Usage

The agent uses two LLM models:

1. **Creative Model** (temperature=0.7): For generating descriptions and pitches
2. **Reasoning Model** (temperature=0.0): For structured decisions (currently unused in v2)

---

## Configuration

### Environment Variables

```bash
# LLM Models
LLM_CREATIVE_MODEL=claude-3-5-haiku-20241022
LLM_REASONING_MODEL=claude-sonnet-4-5-20250929

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
| Transparency | Limited | Full reasoning logs |
| Search Strategy | Fixed | Adaptive (relaxes constraints) |
| Complexity | Simple | Moderate |
| Reliability | High | High |
| User Interrupts | 2 max | 2 max |

### When to Use v2 vs v3

**Use v2 if:**
- You want predictable, deterministic behavior
- You want to minimize LLM API calls
- You have a simple, well-defined flow

**Use v3 if:**
- You want the agent to adapt to different scenarios
- You want transparent decision-making
- You want automatic loop prevention
- You want the agent to handle edge cases intelligently

---

## Changelog

### Version 3.0 (2025-11-30)
- Introduced supervisor pattern with LLM-powered decision making
- Automatic loop prevention and max iteration limits
- Adaptive search strategy (relaxes constraints on retry)
- Comprehensive error handling for all edge cases
- Full test coverage (13 tests, 100% passing)
- Complete documentation with examples

### Version 2.0 (2025-11-30)
- Removed supervisor node (deterministic flow)
- Simplified state machine
- Fixed "knows all" edge case
- Added automatic re-search
- Improved error handling

### Version 1.0 (2025-11-29)
- Initial release with basic flow
- Vibe selection
- Artist knowledge check
- LLM-powered pitches

---

## Support

For issues or questions, contact the development team or file an issue in the repository.
