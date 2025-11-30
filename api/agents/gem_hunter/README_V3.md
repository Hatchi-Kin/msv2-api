# Music Curator Agent v3

A truly agentic LangGraph system that autonomously curates personalized playlists using an LLM-powered supervisor.

## Quick Start

### Starting the Agent

```python
from api.agents.gem_hunter.graph_v3 import build_agent_graph_v3
from api.agents.gem_hunter.state_v3 import AgentState

# Build graph
app = build_agent_graph_v3(pool, checkpointer=checkpointer)

# Initial state
initial_state: AgentState = {
    "playlist_id": "123",
    "user_id": "user1",
    "playlist_analyzed": False,
    "vibe_choice": None,
    "search_iteration": 0,
    "knowledge_checked": False,
    "results_presented": False,
    "playlist_profile": None,
    "candidate_tracks": [],
    "quality_assessment": None,
    "known_artists": [],
    "next_action": "",
    "supervisor_reasoning": "",
    "tool_parameters": {},
    "action_history": [],
    "iteration_count": 0,
    "ui_state": None,
    "error": None,
}

# Run
config = {"configurable": {"thread_id": "playlist_123"}}
final_state = await app.ainvoke(initial_state, config=config)
ui_state = final_state.get("ui_state")
```

### Resuming After User Input

```python
# User selected vibe
await app.aupdate_state(config, {"vibe_choice": "energy"})
final_state = await app.ainvoke(None, config=config)

# User selected known artists
await app.aupdate_state(config, {"known_artists": ["Artist A", "Artist B"]})
final_state = await app.ainvoke(None, config=config)
```

## Architecture

```
START → SUPERVISOR → [Tool] → SUPERVISOR → [Tool] → ... → END
```

The supervisor makes all routing decisions based on current state.

## Key Features

### 1. Autonomous Decision Making
The supervisor uses an LLM to analyze state and decide the next action:
```python
decision = await llm.with_structured_output(SupervisorDecision).ainvoke(context)
# Returns: next_action, reasoning, parameters
```

### 2. Adaptive Search Strategy
Search automatically relaxes constraints on retry:
```python
if iteration > 1:
    constraints["min_bpm"] = max(0, constraints["min_bpm"] - 10)
    constraints["max_bpm"] = constraints["max_bpm"] + 10
```

### 3. Loop Prevention
Detects same action 3x in a row:
```python
if len(history) >= 3 and len(set(history[-3:])) == 1:
    return {"next_action": "present_results"}  # Break loop
```

### 4. Max Iterations
Safety limit of 10 iterations:
```python
if iteration >= 10:
    return {"next_action": "present_results"}  # Force end
```

## Tools

### analyze_playlist
- Fetches playlist stats
- Validates >= 5 tracks
- Generates description
- **INTERRUPTS** for vibe selection

### search_tracks
- Vector similarity search
- Applies vibe constraints
- Excludes known artists
- Adaptive strategy

### evaluate_results
- Quantity score
- Quality score
- Diversity score
- Overall assessment

### check_knowledge
- Extracts unique artists
- **INTERRUPTS** for artist selection

### present_results
- Filters by known artists
- Selects top 5 tracks
- Generates pitches
- Returns final UI

## Decision Rules

The supervisor follows these rules:

```
✓ Playlist not analyzed → analyze_playlist
✓ Vibe selected, no candidates → search_tracks
✓ Candidates exist, not evaluated → evaluate_results
✓ Quality poor, search_iter < 3 → search_tracks (retry)
✓ Quality good, knowledge not checked → check_knowledge
✓ Knowledge checked, 5+ unknown → present_results
✓ User knows all, search_iter == 1 → search_tracks (with exclusions)
✓ User knows all, search_iter > 1 → present_results (give up)
✓ Stuck or iteration >= 10 → present_results (force end)
```

## Testing

### Unit Tests
```bash
pytest tests/test_supervisor_v3.py -v
pytest tests/test_tools_v3.py -v
```

### Integration Tests
```bash
pytest tests/test_integration_v3.py -v
```

### Manual Testing
```bash
python tests/manual_agent_test_v3.py
```

## Monitoring

### Supervisor Reasoning
Check logs for supervisor decisions:
```
🧠 Supervisor thinking...
✅ Decision: search_tracks
   Reasoning: Vibe selected but no candidates, must search
```

### Action History
Track what the agent is doing:
```python
state["action_history"]  # Last 3 actions
state["iteration_count"]  # Current iteration
state["supervisor_reasoning"]  # Why this action
```

### Quality Assessment
Monitor search quality:
```python
state["quality_assessment"]
# {
#   "sufficient": True,
#   "quality_score": 0.8,
#   "recommendation": "proceed"
# }
```

## Error Handling

### Empty Playlist
```python
if track_count < 5:
    return {
        "error": "Playlist has only 2 tracks...",
        "ui_state": {"message": "Your playlist needs more tracks!"}
    }
```

### No Candidates
```python
if len(candidates) == 0:
    return {
        "ui_state": {
            "message": "I couldn't find any tracks matching your criteria..."
        }
    }
```

### LLM Failure
```python
except Exception as e:
    return {
        "next_action": "present_results",
        "supervisor_reasoning": f"Error: {e}"
    }
```

## Configuration

### Environment Variables
```bash
LLM_CREATIVE_MODEL=claude-3-5-haiku-20241022
LLM_REASONING_MODEL=claude-sonnet-4-5-20250929
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=...
```

### Tuning Parameters

**Search limits:**
```python
limit = 50 if iteration == 1 else 100
```

**Quality threshold:**
```python
assessment = {"sufficient": overall > 0.6}
```

**Max iterations:**
```python
if iteration >= 10:  # Adjust if needed
```

## Documentation

- **Complete Guide**: `AGENT_DOCUMENTATION_V3.md`
- **Migration Guide**: `MIGRATION_V2_TO_V3.md`
- **Implementation Summary**: `.kiro/specs/music-curator-agent/IMPLEMENTATION_SUMMARY.md`

## Files

### Core Implementation
- `state_v3.py` - State definitions
- `graph_v3.py` - LangGraph structure
- `nodes/supervisor_v3.py` - Supervisor node
- `nodes/tools_v3.py` - Tool nodes

### Tests
- `tests/test_supervisor_v3.py` - Supervisor tests
- `tests/test_tools_v3.py` - Tool tests
- `tests/test_integration_v3.py` - Integration tests
- `tests/manual_agent_test_v3.py` - Manual testing script

### Documentation
- `AGENT_DOCUMENTATION_V3.md` - Complete documentation
- `MIGRATION_V2_TO_V3.md` - Migration guide
- `README_V3.md` - This file

## Support

For issues or questions:
1. Check `AGENT_DOCUMENTATION_V3.md`
2. Review test files for examples
3. Check supervisor reasoning logs
4. File an issue with reproduction steps

## License

[Your License Here]
