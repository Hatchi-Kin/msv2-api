# Music Curator Agent - Design Document

## Overview

A supervisor-based LangGraph agent that autonomously curates personalized playlists. The supervisor makes intelligent decisions about search strategy, quality evaluation, and when to present results. User interaction is limited to 2 questions maximum.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agent                       │
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

## Components

### 1. Supervisor Node

**Purpose:** The brain. Looks at state, reasons about what to do next, picks a tool.

**Input:** Current AgentState

**Output:** 
```python
{
    "next_action": "analyze_playlist" | "search_tracks" | "evaluate_results" | "check_knowledge" | "present_results" | "END",
    "reasoning": "Why I chose this action",
    "parameters": {}  # Tool-specific params
}
```

**Decision Logic (LLM Prompt):**

```
You are a music curator supervisor. Your mission: create a 5-track playlist of hidden gems.

Current State:
- Playlist analyzed: {playlist_analyzed}
- Vibe selected: {vibe_choice}
- Candidates found: {len(candidates)}
- Quality score: {quality_score}
- Known artists checked: {knowledge_checked}
- Known artists: {known_artists}
- Iteration: {iteration}/10

Available Tools:
1. analyze_playlist - Analyze source playlist, ask user for vibe (INTERRUPTS)
2. search_tracks - Search for similar tracks with constraints
3. evaluate_results - Assess quality/quantity of current candidates
4. check_knowledge - Ask which artists user knows (INTERRUPTS)
5. present_results - Show final 5-track playlist (ENDS)

Rules:
- You can only interrupt user TWICE total (analyze + check_knowledge)
- If playlist not analyzed, you MUST call analyze_playlist
- If vibe selected but no candidates, you MUST call search_tracks
- If candidates exist but not evaluated, you SHOULD call evaluate_results
- If quality is poor, you CAN call search_tracks again with different params
- If quality is good and knowledge not checked, you MUST call check_knowledge
- If knowledge checked and you have 5+ unknown tracks, you MUST call present_results
- If user knows all artists and not re-searched yet, you MUST call search_tracks with exclusions
- If stuck (same action 3x), you MUST try different action or present_results

What should you do next?
```

**Loop Prevention:**
- Track last 3 actions
- If same action 3x, force different choice
- Max 10 iterations, then force present_results

### 2. Tool Nodes

#### `analyze_playlist`

**Purpose:** Analyze source playlist, generate description, ask for vibe

**Input:** playlist_id

**Output:**
```python
{
    "playlist_analyzed": True,
    "playlist_profile": {
        "avg_bpm": 120,
        "avg_energy": 0.7,
        "top_genres": ["indie", "rock"],
        "description": "Upbeat indie rock with energetic vibes"
    },
    "ui_state": {
        "message": "I analyzed your playlist...",
        "options": [
            {"label": "🔥 More of this", "value": "similar"},
            {"label": "😌 Chill", "value": "chill"},
            {"label": "⚡ Energy", "value": "energy"},
            {"label": "🌟 Surprise", "value": "surprise"}
        ]
    }
}
```

**INTERRUPTS:** Yes - waits for user to select vibe

---

#### `search_tracks`

**Purpose:** Search for similar tracks using vector similarity + constraints

**Input:** 
- playlist_id
- vibe_choice
- excluded_artists (optional)
- iteration_number (to vary strategy)

**Logic:**
```python
# Base: Get playlist centroid
centroid = get_playlist_centroid(playlist_id)

# Apply vibe constraints
if vibe == "chill":
    constraints = {"max_energy": 0.6, "max_bpm": 110}
elif vibe == "energy":
    constraints = {"min_energy": 0.7, "min_bpm": 120}
elif vibe == "similar":
    constraints = {"min_bpm": avg_bpm - 20, "max_bpm": avg_bpm + 20}
else:  # surprise
    constraints = {}

# Adaptive strategy based on iteration
if iteration == 1:
    limit = 50
elif iteration == 2:
    # Relax constraints by 20%
    constraints = relax_constraints(constraints, 0.2)
    limit = 100
else:
    # Remove constraints, cast wider net
    constraints = {}
    limit = 200

# Search
candidates = vector_search(
    centroid=centroid,
    constraints=constraints,
    exclude_artists=excluded_artists,
    limit=limit
)

return {
    "candidate_tracks": candidates,
    "search_iteration": iteration
}
```

**INTERRUPTS:** No

---

#### `evaluate_results`

**Purpose:** Assess quality and quantity of candidates

**Input:** candidate_tracks

**Logic:**
```python
# Quantity check
quantity_score = min(len(candidates) / 50, 1.0)

# Quality check (similarity scores)
avg_similarity = mean([t.distance for t in candidates])
quality_score = 1.0 - avg_similarity  # Lower distance = higher quality

# Diversity check (unique artists)
unique_artists = len(set(t.artist for t in candidates))
diversity_score = min(unique_artists / 20, 1.0)

# Overall
overall_score = (quantity_score + quality_score + diversity_score) / 3

assessment = {
    "sufficient": overall_score > 0.6,
    "quality_score": overall_score,
    "recommendation": "proceed" if overall_score > 0.6 else "search_again"
}

return {
    "quality_assessment": assessment
}
```

**INTERRUPTS:** No

---

#### `check_knowledge`

**Purpose:** Ask which artists user knows

**Input:** candidate_tracks

**Logic:**
```python
# Extract unique artists
artists = list(set(t.artist for t in candidates[:20]))  # Top 20 only

# Create options
options = [{"label": artist, "value": artist} for artist in artists]
options.append({"label": "None", "value": "none"})
options.append({"label": "All", "value": "all"})

return {
    "knowledge_checked": True,
    "ui_state": {
        "message": "Which of these artists do you know?",
        "options": options
    }
}
```

**INTERRUPTS:** Yes - waits for user to select artists

---

#### `present_results`

**Purpose:** Select final 5 tracks, generate pitches, present

**Input:** 
- candidate_tracks
- known_artists
- playlist_profile

**Logic:**
```python
# Filter out known artists
unknown_tracks = [t for t in candidates if t.artist not in known_artists]

# If not enough unknown, include some known
if len(unknown_tracks) < 5:
    final_tracks = unknown_tracks + candidates[:5 - len(unknown_tracks)]
else:
    final_tracks = unknown_tracks[:5]

# Generate pitches with LLM
for track in final_tracks:
    pitch = llm.generate_pitch(track, playlist_profile)
    track.reason = pitch

# Generate overall justification
justification = llm.generate_justification(
    final_tracks, 
    playlist_profile,
    known_artists
)

return {
    "results_presented": True,
    "ui_state": {
        "message": justification,
        "cards": [
            {
                "id": t.id,
                "title": t.title,
                "artist": t.artist,
                "reason": t.reason
            } for t in final_tracks
        ]
    }
}
```

**INTERRUPTS:** No (final state)

---

## State Management

```python
class AgentState(TypedDict):
    # Input
    playlist_id: str
    user_id: str
    
    # Flow Control
    playlist_analyzed: bool
    vibe_choice: Optional[str]
    search_iteration: int
    knowledge_checked: bool
    results_presented: bool
    
    # Data
    playlist_profile: Dict[str, Any]
    candidate_tracks: List[Track]
    quality_assessment: Optional[Dict]
    known_artists: List[str]
    
    # Supervisor Control
    next_action: str
    supervisor_reasoning: str
    action_history: List[str]  # Last 3 actions for loop detection
    iteration_count: int
    
    # UI
    ui_state: Optional[Dict]
```

## Graph Structure

```python
def build_graph(pool):
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("analyze_playlist", analyze_node)
    workflow.add_node("search_tracks", search_node)
    workflow.add_node("evaluate_results", evaluate_node)
    workflow.add_node("check_knowledge", knowledge_node)
    workflow.add_node("present_results", present_node)
    
    # Start -> Supervisor
    workflow.add_edge(START, "supervisor")
    
    # Supervisor routes to tools
    def route_supervisor(state):
        action = state["next_action"]
        if action == "END":
            return END
        return action
    
    workflow.add_conditional_edges("supervisor", route_supervisor)
    
    # All tools return to supervisor
    workflow.add_edge("analyze_playlist", "supervisor")
    workflow.add_edge("search_tracks", "supervisor")
    workflow.add_edge("evaluate_results", "supervisor")
    workflow.add_edge("check_knowledge", "supervisor")
    workflow.add_edge("present_results", END)
    
    # Compile with interrupts
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_after=["analyze_playlist", "check_knowledge"]
    )
```

## Edge Cases

### User Knows All Artists

**Scenario:** User selects "All" in knowledge check

**Supervisor Decision:**
```python
if known_artists == "all" and not re_searched:
    # Add all to exclusion list, search again
    next_action = "search_tracks"
    parameters = {"excluded_artists": all_artists}
else:
    # Already re-searched, present what we have
    next_action = "present_results"
```

### Poor Quality Results

**Scenario:** evaluate_results returns quality_score < 0.6

**Supervisor Decision:**
```python
if search_iteration < 3:
    # Try again with relaxed constraints
    next_action = "search_tracks"
else:
    # Present best available
    next_action = "present_results"
```

### No Results Found

**Scenario:** search_tracks returns 0 candidates

**Supervisor Decision:**
```python
if search_iteration == 1:
    # Try with no constraints
    next_action = "search_tracks"
else:
    # Present error, ask to try different vibe
    next_action = "present_results"  # With error message
```

## Testing Strategy

### Unit Tests

1. Test each tool in isolation with mock state
2. Test supervisor decision logic with various states
3. Test loop detection mechanism

### Integration Tests

1. Full flow: analyze → search → evaluate → check → present
2. Re-search flow: check (all known) → search → present
3. Poor quality flow: search → evaluate (poor) → search → present

### Property Tests

**Property 1:** Supervisor never calls same tool more than 3 times in a row
**Property 2:** User is never interrupted more than 2 times
**Property 3:** Agent always reaches END within 10 iterations
**Property 4:** Final playlist always has 1-5 tracks
**Property 5:** If user knows none, final tracks contain 0 known artists

## Implementation Plan

See tasks.md

