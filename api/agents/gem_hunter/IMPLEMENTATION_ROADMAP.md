# Job-Getting Agent: Implementation Roadmap

## Current State Assessment

### What You Have (Good Foundation)
✅ LangGraph-based agent with 3 nodes (Discovery, Analysis, Presentation)
✅ Vector similarity search with centroid calculation
✅ Human-in-the-loop interactions (knowledge check, vibe selection)
✅ LLM-powered pitch generation and justifications
✅ Audio features being populated (BPM, energy, brightness, harmonic_ratio, etc.)
✅ Clean separation of concerns (nodes, tools, LLM modules)

### What's Missing (To Impress Recruiters)
❌ **True Agency** - Agent follows a fixed pipeline, doesn't make decisions
❌ **Tool Usage** - No @tool decorators, no dynamic tool selection
❌ **Streaming** - User sees nothing while agent thinks
❌ **Observability** - Hard to debug, no step-by-step visibility
❌ **Audio Feature Integration** - New metrics aren't used yet
❌ **Advanced Reasoning** - No planning, no self-correction

---

## The Plan: 3 Phases to "Job-Getting" Level

### Phase 1: Add True Agency (Supervisor Pattern) - **HIGH IMPACT**
**Goal:** Make the agent *decide* what to do next instead of following a script.

**Implementation:**
1. Create a `SupervisorNode` that uses an LLM to decide next steps
2. Convert existing logic into `@tool` decorated functions
3. Refactor graph to route through Supervisor

**Why This Impresses:**
- Shows understanding of agentic AI (planning, reasoning)
- Demonstrates LangChain/LangGraph tool usage patterns
- Proves you can build adaptable systems, not just scripts

**Time Estimate:** 4-6 hours

---

### Phase 2: Integrate Audio Features & Improve Justifications - **MEDIUM IMPACT**
**Goal:** Use the new audio metrics to make better recommendations and explain them.

**Implementation:**
1. Add audio feature filtering to repository queries
2. Update agent to use BPM/energy/brightness in decision-making
3. Enhance justifications with actual numbers ("This track has 142 BPM...")
4. Create a "Taste Profile" summary for the user

**Why This Impresses:**
- Shows you can work with real data, not just mock examples
- Demonstrates domain knowledge (music/audio analysis)
- Proves you can explain AI decisions (explainability)

**Time Estimate:** 3-4 hours

---

### Phase 3: Add Streaming & Observability - **MEDIUM-HIGH IMPACT**
**Goal:** Show the user what the agent is doing in real-time.

**Implementation:**
1. Implement LangGraph streaming (`stream_mode="values"`)
2. Send progress updates to frontend ("Searching database...", "Analyzing 15 tracks...")
3. Add LangSmith tracing (optional but impressive)
4. Create a debug mode that shows agent's reasoning

**Why This Impresses:**
- Shows you understand production concerns (UX, debugging)
- Demonstrates async/streaming patterns
- Proves you think about the full user experience

**Time Estimate:** 3-4 hours

---

## Phase 1 Deep Dive: Supervisor Pattern

### Current Flow (Fixed Pipeline)
```
START → Discovery → Analysis → Presentation → END
```

### New Flow (Supervisor Decides)
```
START → Supervisor → [Decides] → Tool → Supervisor → [Decides] → Tool → ... → END
```

### Architecture

```python
# supervisor_node.py
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal

class SupervisorDecision(BaseModel):
    """Supervisor's decision on what to do next."""
    next_action: Literal[
        "search_tracks",
        "filter_by_audio",
        "check_artist_knowledge", 
        "present_results",
        "ask_user"
    ]
    reasoning: str = Field(description="Why this action makes sense")
    parameters: dict = Field(default_factory=dict)

async def supervisor_node(state: AgentState) -> dict:
    """
    The brain of the agent. Decides what to do next based on current state.
    """
    # Build context for LLM
    context = f"""
You are a music curator AI. Your goal: find hidden gems for the user.

Current State:
- Playlist analyzed: {state.get('playlist_analysis', 'Not yet')}
- Candidates found: {len(state.get('candidate_tracks', []))}
- Enriched tracks: {len(state.get('enriched_tracks', []))}
- User constraints: {state.get('constraints', {})}
- Known artists: {state.get('known_artists', [])}

Available Actions:
1. search_tracks - Find similar tracks using vector search
2. filter_by_audio - Filter tracks by BPM, energy, brightness
3. check_artist_knowledge - Ask user which artists they know
4. present_results - Show final recommendations
5. ask_user - Ask a clarifying question

What should you do next?
"""
    
    llm = get_llm(model=settings.LLM_REASONING_MODEL, temperature=0)
    decision = await llm.with_structured_output(SupervisorDecision).ainvoke(context)
    
    return {
        "next_action": decision.next_action,
        "supervisor_reasoning": decision.reasoning
    }
```

### Tools (Workers)

```python
# tools/search_tools.py
from langchain_core.tools import tool

@tool
async def search_similar_tracks(
    centroid: list[float],
    exclude_ids: list[int],
    exclude_artists: list[str],
    limit: int = 10
) -> list[dict]:
    """
    Find tracks similar to the playlist centroid.
    
    Args:
        centroid: The average embedding vector of the playlist
        exclude_ids: Track IDs to exclude
        exclude_artists: Artist names to exclude
        limit: Maximum number of tracks to return
    """
    repo = LibraryRepository(pool)
    results = await repo.search_hidden_gems(centroid, exclude_ids, exclude_artists, limit)
    return [track.model_dump() for track, distance in results]

@tool
async def filter_tracks_by_audio_features(
    tracks: list[dict],
    min_bpm: float = 0,
    max_bpm: float = 300,
    min_energy: float = 0,
    max_energy: float = 1,
    min_brightness: float = 0,
    max_brightness: float = 10000,
    harmonic_ratio_preference: str = "any"  # "melodic", "percussive", "any"
) -> list[dict]:
    """
    Filter tracks based on audio features.
    
    Args:
        tracks: List of track dictionaries
        min_bpm, max_bpm: BPM range
        min_energy, max_energy: Energy range (0-1)
        min_brightness, max_brightness: Brightness range (Hz)
        harmonic_ratio_preference: "melodic" (>0.6), "percussive" (<0.4), or "any"
    """
    filtered = []
    for track in tracks:
        # Skip if missing features
        if not all(track.get(f) is not None for f in ['bpm', 'energy', 'brightness', 'harmonic_ratio']):
            continue
        
        # BPM filter
        if not (min_bpm <= track['bpm'] <= max_bpm):
            continue
        
        # Energy filter
        if not (min_energy <= track['energy'] <= max_energy):
            continue
        
        # Brightness filter
        if not (min_brightness <= track['brightness'] <= max_brightness):
            continue
        
        # Harmonic ratio filter
        if harmonic_ratio_preference == "melodic" and track['harmonic_ratio'] < 0.6:
            continue
        if harmonic_ratio_preference == "percussive" and track['harmonic_ratio'] > 0.4:
            continue
        
        filtered.append(track)
    
    return filtered

@tool
async def analyze_playlist_vibe(playlist_id: int) -> dict:
    """
    Analyze a playlist's musical characteristics.
    
    Returns:
        Dictionary with average BPM, energy, brightness, dominant genres, etc.
    """
    repo = LibraryRepository(pool)
    tracks = await repo.get_playlist_sample(playlist_id, max_tracks=20)
    
    # Calculate averages
    avg_bpm = sum(t.get('bpm', 0) for t in tracks if t.get('bpm')) / len(tracks)
    avg_energy = sum(t.get('energy', 0) for t in tracks if t.get('energy')) / len(tracks)
    avg_brightness = sum(t.get('brightness', 0) for t in tracks if t.get('brightness')) / len(tracks)
    
    # Extract genres
    all_genres = []
    for track in tracks:
        if track.get('top_5_genres'):
            all_genres.extend(track['top_5_genres'].split(','))
    
    from collections import Counter
    top_genres = [g for g, _ in Counter(all_genres).most_common(5)]
    
    return {
        "avg_bpm": round(avg_bpm, 1),
        "avg_energy": round(avg_energy, 3),
        "avg_brightness": round(avg_brightness, 1),
        "top_genres": top_genres,
        "track_count": len(tracks)
    }
```

### Updated Graph

```python
# graph.py
from langgraph.graph import StateGraph, START, END

def build_agent_graph(pool: asyncpg.Pool):
    workflow = StateGraph(AgentState)
    
    # Add Supervisor
    workflow.add_node("supervisor", supervisor_node)
    
    # Add Tool Nodes
    workflow.add_node("search_tracks", search_tracks_node)
    workflow.add_node("filter_audio", filter_audio_node)
    workflow.add_node("check_knowledge", check_knowledge_node)
    workflow.add_node("present", presentation_node)
    
    # Entry point
    workflow.add_edge(START, "supervisor")
    
    # Supervisor routes to tools
    def route_supervisor(state: AgentState):
        action = state.get("next_action")
        if action == "search_tracks":
            return "search_tracks"
        elif action == "filter_by_audio":
            return "filter_audio"
        elif action == "check_artist_knowledge":
            return "check_knowledge"
        elif action == "present_results":
            return "present"
        else:
            return END
    
    workflow.add_conditional_edges("supervisor", route_supervisor)
    
    # All tools loop back to supervisor
    workflow.add_edge("search_tracks", "supervisor")
    workflow.add_edge("filter_audio", "supervisor")
    workflow.add_edge("check_knowledge", "supervisor")
    workflow.add_edge("present", END)
    
    return workflow.compile()
```

---

## Quick Wins (Can Do Today)

### 1. Add Audio Feature Display to Frontend
Update `AgentMessage.tsx` to show metrics:

```tsx
{track.bpm && (
  <div className="metrics">
    <span>BPM: {track.bpm}</span>
    <span>Energy: {(track.energy * 100).toFixed(0)}%</span>
    <span>Vibe: {track.brightness > 3000 ? 'Bright' : 'Dark'}</span>
  </div>
)}
```

### 2. Update Justification to Use Real Metrics
In `justification_generator.py`, add metrics to the prompt:

```python
prompt = f"""
Analyze these tracks:
{tracks_with_metrics}

Example: "Track 1 has a driving tempo of 142 BPM and high energy (0.85), 
making it perfect for your 'energetic' preference."
"""
```

### 3. Add a "Taste Profile" Summary
Create a new LLM call that summarizes the user's playlist:

```python
profile = f"""
Your playlist vibe:
- Average BPM: {avg_bpm}
- Energy Level: {'High' if avg_energy > 0.7 else 'Medium' if avg_energy > 0.4 else 'Chill'}
- Sonic Character: {'Bright' if avg_brightness > 3000 else 'Dark'}
- Top Genres: {', '.join(top_genres)}
"""
```

---

## Recommended Order

**This Weekend:**
1. ✅ Finish audio feature extraction (running now)
2. 🎯 Add audio feature display to frontend (1 hour)
3. 🎯 Update justifications to use metrics (1 hour)
4. 🎯 Test the agent with real data

**Next Week:**
1. 🎯 Implement Supervisor pattern (Phase 1) - 4-6 hours
2. 🎯 Add streaming updates (Phase 3) - 3-4 hours
3. 🎯 Polish UI and add "Taste Profile" summary

**Result:** A truly impressive agent that:
- Makes intelligent decisions
- Explains itself with real data
- Shows its work in real-time
- Demonstrates production-level thinking

---

## Questions to Consider

1. **Do you want to start with the Supervisor pattern, or add audio features to the current agent first?**
2. **Should we add streaming next, or focus on decision-making?**
3. **Do you want me to create a detailed code example for any specific part?**

Let me know what you want to tackle first!
