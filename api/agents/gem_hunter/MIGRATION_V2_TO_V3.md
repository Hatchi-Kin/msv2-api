# Migration Guide: v2 to v3

## Overview

This guide helps you migrate from the Music Curator Agent v2 (state machine) to v3 (supervisor pattern).

## What Changed

### Architecture
- **v2**: Deterministic state machine with hardcoded flow
- **v3**: Supervisor pattern with LLM-powered decision making

### State Structure
- **v2**: Had many intermediate flags (`vibe_selected`, `search_done`, `enriched`, `filtered`, etc.)
- **v3**: Simplified to essential flags + supervisor control fields

### Flow Control
- **v2**: Hardcoded edges between nodes
- **v3**: Supervisor decides next action dynamically

## Breaking Changes

### 1. State Fields Removed

These fields no longer exist in v3:
- `vibe_selected` → Use `vibe_choice is not None`
- `search_done` → Use `search_iteration > 0`
- `enriched` → Removed (tracks come enriched from DB)
- `filtered` → Removed (filtering happens in present_results)
- `knowledge_search_attempted` → Use `search_iteration > 1`
- `excluded_artists` → Use `known_artists` (same list)
- `constraints` → Computed dynamically in search_tracks
- `enriched_tracks` → Removed
- `final_tracks` → Removed

### 2. State Fields Added

New fields in v3:
- `next_action`: Tool name or "END"
- `supervisor_reasoning`: Why supervisor chose this action
- `tool_parameters`: Parameters for next tool
- `action_history`: Last 3 actions for loop detection
- `search_iteration`: Number of search attempts
- `quality_assessment`: Quality score from evaluate_results

### 3. Graph Structure

**v2 Graph:**
```python
workflow.add_edge(START, "analyze_playlist")
workflow.add_edge("analyze_playlist", "search_tracks")
workflow.add_edge("search_tracks", "enrich_tracks")
# ... hardcoded edges
```

**v3 Graph:**
```python
workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges("supervisor", route_supervisor)
workflow.add_edge("analyze_playlist", "supervisor")
workflow.add_edge("search_tracks", "supervisor")
# ... all tools return to supervisor
```

### 4. Handler Changes

**v2 Handler:**
```python
from api.agents.gem_hunter.graph import build_agent_graph
from api.agents.gem_hunter.state import UIState
```

**v3 Handler:**
```python
from api.agents.gem_hunter.graph_v3 import build_agent_graph_v3
from api.agents.gem_hunter.state_v3 import AgentState
```

## Migration Steps

### Step 1: Update Imports

Replace all imports:
```python
# Old
from api.agents.gem_hunter.graph import build_agent_graph
from api.agents.gem_hunter.state import AgentState, UIState

# New
from api.agents.gem_hunter.graph_v3 import build_agent_graph_v3
from api.agents.gem_hunter.state_v3 import AgentState
```

### Step 2: Update Initial State

**v2 Initial State:**
```python
initial_state = {
    "messages": [],
    "playlist_id": playlist_id,
    "user_preferences": "General Vibe",
    "excluded_ids": [],
    "centroid": None,
    "candidate_tracks": [],
    "enriched_tracks": [],
    "ui_state": None,
    "next_step": None,
    "knowledge_checked": False,
    "vibe_checked": False,
    "vibe_choice": None,
    "fun_fact_1": None,
    "fun_fact_2": None,
}
```

**v3 Initial State:**
```python
initial_state: AgentState = {
    "playlist_id": str(playlist_id),
    "user_id": "default",
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
```

### Step 3: Update Resume Handler

**v2 Resume Actions:**
- `set_vibe`
- `submit_knowledge`
- `mark_known`
- `continue`
- `add`

**v3 Resume Actions:**
- `set_vibe` (same)
- `submit_knowledge` (same, but handles "none"/"all" differently)
- `add` (same)

**Removed actions:**
- `mark_known` → Use `submit_knowledge` with single artist
- `continue` → Use `submit_knowledge` with `["none"]`

### Step 4: Update State Updates

**v2:**
```python
await app.aupdate_state(config, {
    "vibe_checked": True,
    "vibe_choice": vibe,
    "next_step": "presentation"
})
```

**v3:**
```python
await app.aupdate_state(config, {
    "vibe_choice": vibe
})
# Supervisor decides next step automatically
```

### Step 5: Test Thoroughly

Run the test suite:
```bash
pytest tests/test_supervisor_v3.py tests/test_tools_v3.py tests/test_integration_v3.py -v
```

Run manual tests:
```bash
python tests/manual_agent_test_v3.py
```

## Backward Compatibility

### Running Both Versions

You can run both v2 and v3 simultaneously:

```python
# v2
from api.agents.gem_hunter.graph import build_agent_graph
app_v2 = build_agent_graph(pool)

# v3
from api.agents.gem_hunter.graph_v3 import build_agent_graph_v3
app_v3 = build_agent_graph_v3(pool)
```

Use different thread IDs:
```python
# v2
thread_id = f"playlist_{playlist_id}_v2"

# v3
thread_id = f"playlist_{playlist_id}_v3"
```

### Gradual Migration

1. **Week 1**: Deploy v3 alongside v2, route 10% of traffic to v3
2. **Week 2**: Monitor metrics, increase to 50% if stable
3. **Week 3**: Route 100% to v3
4. **Week 4**: Remove v2 code

## Benefits of v3

### For Users
- More intelligent recommendations
- Better handling of edge cases
- Faster when results are good (skips unnecessary steps)

### For Developers
- Easier to add new tools
- Transparent decision-making (logs reasoning)
- Automatic loop prevention
- Better error handling

## Troubleshooting

### Issue: Agent loops infinitely

**v2**: Had to manually add checks in each node
**v3**: Automatic loop detection (same action 3x → force present_results)

### Issue: Agent makes wrong decision

**v2**: Had to change hardcoded flow
**v3**: Update supervisor prompt or decision rules

### Issue: Need to add new tool

**v2**: Add node + update all edges
**v3**: Add tool + add to supervisor's available tools list

## Support

For questions or issues:
1. Check `AGENT_DOCUMENTATION_V3.md`
2. Review test files for examples
3. Check supervisor reasoning logs
4. File an issue with reproduction steps

## Rollback Plan

If you need to rollback to v2:

1. Revert handler imports:
```python
from api.agents.gem_hunter.graph import build_agent_graph
```

2. Revert initial state structure

3. Restart service

4. Monitor for any state corruption (different thread IDs prevent this)
