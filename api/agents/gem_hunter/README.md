# Music Curator Agent (Gem Hunter)

**Version:** 3.0  
**Status:** ✅ Production Ready

## Overview

An intelligent music recommendation agent that curates personalized playlists of "hidden gems" - tracks the user hasn't heard before that match their taste. Uses LangGraph with a supervisor pattern for true agentic behavior.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      SUPERVISOR                              │
│  (LLM-powered decision maker - decides next action)         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │ ANALYZE │        │ SEARCH  │        │ EVALUATE│
   │PLAYLIST │───────▶│ TRACKS  │───────▶│ RESULTS │
   └─────────┘        └─────────┘        └─────────┘
        │                                       │
        │ (user selects vibe)                  │
        ▼                                       ▼
   ┌─────────┐                           ┌─────────┐
   │  CHECK  │◀──────────────────────────│ PRESENT │
   │KNOWLEDGE│                           │ RESULTS │
   └─────────┘                           └─────────┘
        │
        │ (user marks known artists)
        ▼
   ┌─────────┐
   │ PRESENT │
   │ RESULTS │
   └─────────┘
```

## Key Features

- **True Agentic Behavior**: LLM supervisor makes intelligent decisions based on state
- **2 User Interrupts**: Vibe selection + artist knowledge check
- **Evidence-Based Recommendations**: Tracks include detailed metric comparisons
- **Parallel LLM Calls**: Optimized for speed (5 track pitches + 2 justifications in parallel)
- **Loop Prevention**: Automatic detection and breaking of infinite loops
- **Graceful Error Handling**: Handles all edge cases with clear user messages

## File Structure

```
api/agents/gem_hunter/
├── README.md                    # This file
├── graph_v3.py                  # LangGraph workflow definition
├── state_v3.py                  # State TypedDict definitions
├── llm_factory.py               # LLM initialization
├── exceptions.py                # Custom exceptions
├── nodes/
│   ├── supervisor_v3.py         # Supervisor decision logic
│   └── tools_v3.py              # Tool implementations
├── tools/
│   └── search_tool.py           # Database search utilities
└── docs/
    ├── FRONTEND_INTEGRATION_GUIDE.md
    ├── MIGRATION_V2_TO_V3.md
    └── KNOWN_ISSUES.md
```

## Quick Start

### Backend

```python
from api.agents.gem_hunter.graph_v3 import build_agent_graph_v3
from langgraph.checkpoint.memory import MemorySaver

# Build graph
checkpointer = MemorySaver()
app = build_agent_graph_v3(pool, checkpointer=checkpointer)

# Start agent
config = {"configurable": {"thread_id": f"playlist_{playlist_id}"}}
initial_state = {
    "playlist_id": str(playlist_id),
    "user_id": "default",
    "playlist_analyzed": False,
    # ... other fields
}
result = await app.ainvoke(initial_state, config=config)
ui_state = result.get("ui_state")
```

### Frontend

```typescript
// Start agent
const response = await fetch('/agent/recommend/123', { method: 'POST' });
const uiState = await response.json();

// Resume with user action
await fetch('/agent/resume', {
  method: 'POST',
  body: JSON.stringify({
    action: 'set_vibe',
    playlist_id: 123,
    payload: { vibe: 'similar' }
  })
});
```

## Agent Flow

1. **Analyze Playlist** (automatic)
   - Calculates audio feature averages (BPM, energy, brightness, etc.)
   - Generates vibe description
   - Asks user to select desired vibe
   - **User interruption #1**

2. **Search Tracks** (automatic)
   - Searches library using vector similarity
   - Applies vibe-based constraints
   - Returns 50 candidates

3. **Evaluate Results** (automatic)
   - Assesses quality and quantity
   - Decides if more searching needed

4. **Check Knowledge** (automatic)
   - Extracts unique artists from candidates
   - Asks user which artists they know
   - **User interruption #2**

5. **Present Results** (automatic)
   - Filters out known artists
   - Selects top 5 tracks
   - Generates evidence-based justifications
   - Returns structured Understanding + Selection

## State Management

The agent uses LangGraph's checkpointing for state persistence:

```python
class AgentState(TypedDict):
    # Input
    playlist_id: str
    user_id: str
    
    # Flow control
    playlist_analyzed: bool
    vibe_choice: Optional[str]
    search_iteration: int
    knowledge_checked: bool
    results_presented: bool
    
    # Data
    playlist_profile: Dict[str, Any]
    candidate_tracks: List[Track]
    known_artists: List[str]
    
    # Supervisor
    next_action: str
    supervisor_reasoning: str
    action_history: List[str]
    iteration_count: int
    
    # UI
    ui_state: UIState
    error: Optional[str]
```

## UI State Structure

```typescript
interface UIState {
  message: string;              // Main message to display
  understanding?: string;       // Part 1: Playlist understanding
  selection?: string;           // Part 2: Track selection reasoning
  options: ButtonOption[];      // User action buttons
  cards: TrackCard[];          // Recommended tracks
  thought_process: string[];   // Internal reasoning (optional)
}
```

## Performance Optimizations

- **Parallel LLM calls**: 5 track pitches + 2 justifications run simultaneously
- **Rule-based descriptions**: Playlist vibe description uses fast rules instead of LLM
- **Efficient vector search**: Uses pgvector with proper indexing
- **Expected latency**: 4-6 seconds for final results (down from 14-21 seconds)

## Configuration

Environment variables (`.env`):

```bash
# LLM Configuration
LLM_PROVIDER=anthropic
LLM_REASONING_MODEL=claude-sonnet-4-5-20250929
LLM_CREATIVE_MODEL=claude-3-5-haiku-20241022
ANTHROPIC_API_KEY=your_key_here

# Agent Configuration
MAX_AGENT_ITERATIONS=10
```

## Testing

```bash
# Unit tests
pytest tests/test_supervisor_v3.py
pytest tests/test_tools_v3.py

# Integration test
pytest tests/test_integration_v3.py

# Manual test (with real database)
python tests/manual_agent_test_v3.py
```

## Error Handling

The agent handles:
- Empty playlists (< 5 tracks)
- No candidates found
- User knows all artists
- LLM service unavailable
- Max iterations exceeded
- Infinite loops

All errors result in graceful messages to the user.

## API Endpoints

### Start Agent
```
POST /agent/recommend/{playlist_id}
Response: UIState
```

### Resume Agent
```
POST /agent/resume
Body: {
  action: "set_vibe" | "submit_knowledge",
  playlist_id: number,
  payload: { vibe?: string, known_artists?: string[] }
}
Response: UIState
```

## Migration from V2

See `docs/MIGRATION_V2_TO_V3.md` for detailed migration guide.

## Known Issues

See `docs/KNOWN_ISSUES.md` for current limitations and workarounds.

## Contributing

When modifying the agent:
1. Update state definitions in `state_v3.py`
2. Add new tools in `nodes/tools_v3.py`
3. Update supervisor decision rules in `nodes/supervisor_v3.py`
4. Update this README
5. Add tests

## License

Proprietary - All rights reserved
