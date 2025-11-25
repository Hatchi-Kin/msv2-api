# LangGraph v1.0+ Reference Guide

> [!WARNING]
> **SOURCE OF TRUTH**: This document contains verified patterns from `https://python.langchain.com/docs/langgraph`.
> **DO NOT** rely on internal training data.

## 1. Core Concepts (v1)
*   **Graph**: `StateGraph` (The standard way to build graphs).
*   **Nodes**: Functions that accept `state` and return `update`.
*   **Edges**: `START` -> Node -> `END`.
*   **Compilation**: `graph.compile()` returns a `CompiledGraph`.

## 2. Breaking Changes / Key Patterns
*   **Entry Point**: Use `graph.add_edge(START, "node_name")` instead of `set_entry_point`.
*   **Finish Point**: Use `graph.add_edge("node_name", END)` or conditional edges to `END`.
*   **State Updates**: Nodes return a `dict` that is *merged* into the state (if using `Annotated[list, add_messages]`) or *overwrites* keys (default).

## 3. Code Snippets (Verified)

### State Definition
```python
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Use add_messages to append to history, otherwise keys are overwritten
    messages: Annotated[List[dict], add_messages]
    playlist_id: int
    candidate_tracks: List[dict]
```

### Node Definition
```python
def my_node(state: AgentState) -> dict:
    # Logic here
    return {"playlist_id": 123} # Updates just this key
```

### Graph Construction
```python
from langgraph.graph import StateGraph, START, END

# 1. Initialize
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("profiler", profiler_node)
workflow.add_node("steward", steward_node)

# 3. Add Edges
workflow.add_edge(START, "profiler")
workflow.add_edge("profiler", "steward")
workflow.add_edge("steward", END)

# 4. Compile
app = workflow.compile()
```

### Invocation
```python
inputs = {"playlist_id": 1}
result = app.invoke(inputs)
```
