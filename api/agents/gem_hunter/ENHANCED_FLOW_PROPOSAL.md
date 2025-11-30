# Enhanced Agent Flow - Design Proposal

**Status:** 📋 Design Phase  
**Target:** 1-3 step user experience with intelligent playlist analysis  
**Goal:** Fast, conversational, and saveable playlist creation

---

## 🎯 Design Philosophy

### Core Principles
1. **Show Your Work** - Agent explains what it understood
2. **Smart Questions** - Use known artists as reference points
3. **Fast Interaction** - Maximum 3 steps from start to save
4. **Click-Only** - No text input, only pre-made choices
5. **Saveable Output** - User can save results as a new playlist

### User Journey
```
Select Playlist → See Analysis → Pick Direction → Refine (optional) → Save Playlist
     (1 click)      (read)         (1 click)        (0-1 click)       (1 click)
```

**Total: 3-4 clicks maximum**

---

## 🔄 Proposed Flow

### **Step 1: Playlist Analysis + Vibe Selection** 🧠

**What Happens:**
1. Agent analyzes the selected playlist
2. Generates natural language description of the vibe
3. Presents contextualized options based on analysis

**Example UI:**

```
┌─────────────────────────────────────────────────────────┐
│ 🎵 Hidden Gem Hunter                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ I analyzed your "Workout Mix" playlist.                 │
│                                                          │
│ 📊 Here's what I found:                                 │
│ • Average BPM: 128 (upbeat, energetic)                  │
│ • Energy Level: High (0.82/1.0)                         │
│ • Top Genres: Electronic, House, Pop                    │
│                                                          │
│ 💭 Vibe: High-energy dance tracks with strong beats     │
│    and electronic production.                           │
│                                                          │
│ What direction should I explore for hidden gems?        │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🔥 More of this energy                              │ │
│ │    (BPM 120-140, High Energy)                       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 😌 Dial it down                                     │ │
│ │    (BPM 90-110, Medium Energy)                      │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🎸 More melodic/guitar-driven                       │ │
│ │    (High harmonic ratio)                            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🥁 More beat-heavy/percussive                       │ │
│ │    (Low harmonic ratio)                             │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🌟 Surprise me (no constraints)                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Backend Implementation:**

```python
# New tool: analyze_playlist_vibe
async def analyze_playlist_vibe(pool, playlist_id):
    # 1. Get playlist sample (20 tracks)
    tracks = await repo.get_playlist_sample(playlist_id, max_tracks=20)
    
    # 2. Calculate stats
    avg_bpm = calculate_average(tracks, 'bpm')
    avg_energy = calculate_average(tracks, 'energy')
    top_genres = extract_top_genres(tracks, limit=3)
    
    # 3. Generate natural language description using LLM
    llm = get_llm(model=settings.LLM_CREATIVE_MODEL, temperature=0.7)
    
    prompt = f"""
    Describe this playlist in 1-2 vivid sentences:
    - Avg BPM: {avg_bpm}
    - Avg Energy: {avg_energy}
    - Top Genres: {', '.join(top_genres)}
    
    Be conversational. Examples:
    - "A mellow selection of acoustic folk with warm male vocals"
    - "High-energy electronic dance tracks with pulsing beats"
    """
    
    description = await llm.ainvoke(prompt)
    
    return {
        "avg_bpm": avg_bpm,
        "avg_energy": avg_energy,
        "top_genres": top_genres,
        "description": description.content.strip()
    }
```

**State Updates:**
```python
{
    "playlist_profile": {
        "avg_bpm": 128,
        "avg_energy": 0.82,
        "top_genres": ["Electronic", "House", "Pop"],
        "description": "High-energy dance tracks..."
    },
    "vibe_constraints": {
        "min_bpm": 120,
        "max_bpm": 140,
        "min_energy": 0.6
    }
}
```

---

### **Step 2A: Smart Artist Knowledge Check** 🎤
*(If user knows some artists from initial search)*

**What Happens:**
1. Agent finds initial candidates
2. Checks which artists user knows
3. Uses those artists' tracks as reference points

**Example UI:**

```
┌─────────────────────────────────────────────────────────┐
│ 🎵 Hidden Gem Hunter                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ I found some tracks you might like!                     │
│                                                          │
│ I see you know these artists:                           │
│ • Tame Impala                                           │
│ • MGMT                                                  │
│ • Phoenix                                               │
│                                                          │
│ Among their songs in your playlist, which vibe are      │
│ you looking for in new discoveries?                     │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🎵 Like "Feels Like We Only Go Backwards"          │ │
│ │    (Tame Impala)                                    │ │
│ │    Dreamy, psychedelic, mid-tempo                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🎵 Like "Electric Feel" (MGMT)                      │ │
│ │    Upbeat, synth-heavy, danceable                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🎵 Like "1901" (Phoenix)                            │ │
│ │    Indie rock, energetic, guitar-driven             │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🔄 None of these, show me something different       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Backend Implementation:**

```python
async def check_knowledge_smart(state: AgentState):
    # 1. Get known artists from initial search
    known_artists = state.get("known_artists", [])
    
    if not known_artists:
        # Fallback to Step 2B
        return await check_knowledge_simple(state)
    
    # 2. Get reference tracks from user's playlist by these artists
    repo = LibraryRepository(self.pool)
    reference_tracks = await repo.get_tracks_by_artists(
        playlist_id=state["playlist_id"],
        artists=known_artists[:3]  # Limit to 3 for UI
    )
    
    # 3. Generate descriptions for each reference track using LLM
    llm = get_llm(model=settings.LLM_CREATIVE_MODEL, temperature=0.7)
    
    options = []
    for track in reference_tracks:
        # Generate vibe description
        prompt = f"""
        Describe the vibe of this song in 3-5 words:
        Title: {track['title']}
        Artist: {track['artist']}
        BPM: {track.get('bpm', 'unknown')}
        Energy: {track.get('energy', 'unknown')}
        
        Examples: "Dreamy, psychedelic, mid-tempo" or "Upbeat, synth-heavy, danceable"
        """
        
        vibe = await llm.ainvoke(prompt)
        
        options.append({
            "label": f"🎵 Like \"{track['title']}\" ({track['artist']})",
            "sublabel": vibe.content.strip(),
            "value": "reference_track",
            "payload": {
                "track_id": track['id'],
                "artist": track['artist'],
                "bpm": track.get('bpm'),
                "energy": track.get('energy')
            }
        })
    
    # Add "none of these" option
    options.append({
        "label": "🔄 None of these, show me something different",
        "value": "skip_reference"
    })
    
    return {
        "ui_state": UIState(
            message="Among their songs in your playlist, which vibe are you looking for?",
            options=options
        ).model_dump()
    }
```

**State Updates:**
```python
{
    "reference_track": {
        "id": 123,
        "artist": "MGMT",
        "bpm": 125,
        "energy": 0.75
    },
    "constraints": {
        # Adjust based on reference track
        "min_bpm": 115,
        "max_bpm": 135,
        "min_energy": 0.65,
        "max_energy": 0.85
    }
}
```
<!-- Melody Gardot, ‐M‐, Têtes Raides, Katie Melua, The Dø -->
Patrice, Xavier Rudd, Les Vieilles Pies, Winston McAnuff, Morcheeba
---

### **Step 2B: Simple Focus Question** 🎹
*(If user knows NO artists from initial search)*

**What Happens:**
1. Agent realizes user doesn't know any artists (perfect for discovery!)
2. Asks a simple focus question to narrow down

**Example UI:**

```
┌─────────────────────────────────────────────────────────┐
│ 🎵 Hidden Gem Hunter                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Great! You don't know any of these artists yet -        │
│ perfect for discovering hidden gems! 🎉                 │
│                                                          │
│ To narrow it down, what's more important to you?        │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🎤 Vocal-focused tracks                             │ │
│ │    Strong vocals and lyrics                         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🎹 Instrumental/production-focused                  │ │
│ │    Emphasis on beats, synths, and production        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⚖️ Balanced mix of both                             │ │
│ │    Equal focus on vocals and production             │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Backend Implementation:**

```python
async def check_knowledge_simple(state: AgentState):
    return {
        "ui_state": UIState(
            message="Great! You don't know any of these artists yet - perfect for discovering hidden gems!\n\nTo narrow it down, what's more important to you?",
            options=[
                {
                    "label": "🎤 Vocal-focused tracks",
                    "sublabel": "Strong vocals and lyrics",
                    "value": "vocal_focus"
                },
                {
                    "label": "🎹 Instrumental/production-focused",
                    "sublabel": "Emphasis on beats, synths, and production",
                    "value": "instrumental_focus"
                },
                {
                    "label": "⚖️ Balanced mix of both",
                    "sublabel": "Equal focus on vocals and production",
                    "value": "balanced"
                }
            ]
        ).model_dump()
    }
```

**Note:** This is a simpler fallback. The focus preference could be used to:
- Filter by `speechiness` (Spotify feature)
- Adjust `instrumentalness` threshold
- Or just be informational for the LLM justification

---

### **Step 3: Final Presentation + Save** 💎

**What Happens:**
1. Agent presents 5 curated tracks
2. Explains reasoning (understanding + selection)
3. Offers save or iterate options

**Example UI:**

```
┌─────────────────────────────────────────────────────────┐
│ 🎵 Hidden Gem Hunter                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 🎵 Understanding:                                       │
│ I searched for high-energy tracks (BPM 120-140) with    │
│ strong beats, similar to your 'Workout Mix' vibe but    │
│ from artists you don't know yet.                        │
│                                                          │
│ 🎵 Selection:                                           │
│ I picked tracks that match the energy of 'Electric      │
│ Feel' by MGMT - upbeat, synth-driven, and danceable.    │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🎵 "Midnight City" by M83                           │ │
│ │    ♫ 105 BPM • ⚡ 0.78 Energy                        │ │
│ │    A soaring synth anthem with infectious energy    │ │
│ │    [▶ Play] [+ Add]                                 │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🎵 "Sleepyhead" by Passion Pit                      │ │
│ │    ♫ 130 BPM • ⚡ 0.82 Energy                        │ │
│ │    Frenetic electro-pop with soaring falsetto       │ │
│ │    [▶ Play] [+ Add]                                 │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [... 3 more tracks ...]                                 │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 💾 Save these 5 tracks as a new playlist            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🔄 Find more tracks like these                      │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🔙 Start over with different preferences            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Backend Implementation:**

```python
async def present_results_enhanced(state: AgentState):
    tracks = state.get("enriched_tracks", [])[:5]
    
    # Generate pitches
    pitches = await generate_pitches(tracks, vibe, user_prefs, llm)
    
    # Generate justification
    justification = await generate_justification(
        tracks, 
        vibe, 
        playlist_id, 
        reference_track=state.get("reference_track"),
        llm
    )
    
    # Create cards with audio features
    cards = []
    for track, pitch in zip(tracks, pitches):
        cards.append(TrackCard(
            id=track['id'],
            title=track['title'],
            artist=track['artist'],
            album=track.get('album'),
            reason=pitch,
            bpm=track.get('bpm'),
            energy=track.get('energy'),
            brightness=track.get('brightness'),
            harmonic_ratio=track.get('harmonic_ratio')
        ))
    
    # Create options
    options = [
        ButtonOption(
            id="save",
            label="💾 Save these 5 tracks as a new playlist",
            action="save_playlist",
            payload={"track_ids": [t['id'] for t in tracks]}
        ),
        ButtonOption(
            id="more",
            label="🔄 Find more tracks like these",
            action="find_more",
            payload={}
        ),
        ButtonOption(
            id="restart",
            label="🔙 Start over with different preferences",
            action="restart",
            payload={}
        )
    ]
    
    return {
        "ui_state": UIState(
            message=f"**Understanding:** {justification.understanding}\n\n**Selection:** {justification.selection}",
            understanding=justification.understanding,
            selection=justification.selection,
            cards=cards,
            options=options
        ).model_dump()
    }
```

---

## 🛠️ New Tools Required

### 1. `analyze_playlist_vibe`
**Purpose:** Generate natural language description of playlist

**Inputs:**
- `playlist_id`

**Outputs:**
```python
{
    "avg_bpm": 128,
    "avg_energy": 0.82,
    "avg_brightness": 3500,
    "top_genres": ["Electronic", "House", "Pop"],
    "description": "High-energy dance tracks with pulsing beats..."
}
```

**Implementation:** See Step 1 above

---

### 2. `get_reference_tracks`
**Purpose:** Get tracks from known artists in user's playlist

**Inputs:**
- `playlist_id`
- `known_artists: List[str]`

**Outputs:**
```python
[
    {
        "id": 123,
        "title": "Electric Feel",
        "artist": "MGMT",
        "bpm": 125,
        "energy": 0.75,
        "vibe_description": "Upbeat, synth-heavy, danceable"
    },
    ...
]
```

**Implementation:**
```python
async def get_reference_tracks(pool, playlist_id, known_artists):
    repo = LibraryRepository(pool)
    
    # Get tracks from these artists in the playlist
    query = """
        SELECT t.id, t.title, t.artist, t.bpm, t.energy, t.harmonic_ratio
        FROM megaset t
        JOIN playlist_tracks pt ON t.id = pt.track_id
        WHERE pt.playlist_id = $1
        AND t.artist = ANY($2::text[])
        LIMIT 5
    """
    
    tracks = await pool.fetch(query, playlist_id, known_artists)
    
    # Generate vibe descriptions using LLM
    llm = get_llm(model=settings.LLM_CREATIVE_MODEL, temperature=0.7)
    
    for track in tracks:
        vibe = await generate_vibe_description(track, llm)
        track['vibe_description'] = vibe
    
    return tracks
```

---

### 3. `save_playlist`
**Purpose:** Create a new playlist with selected tracks

**Inputs:**
- `user_id`
- `track_ids: List[int]`
- `name: str` (optional, auto-generated if not provided)

**Outputs:**
```python
{
    "playlist_id": 456,
    "name": "Hidden Gems - Nov 29",
    "track_count": 5
}
```

**Implementation:**
```python
async def save_playlist(pool, user_id, track_ids, name=None):
    repo = LibraryRepository(pool)
    
    # Auto-generate name if not provided
    if not name:
        from datetime import datetime
        name = f"Hidden Gems - {datetime.now().strftime('%b %d')}"
    
    # Create playlist
    playlist_id = await repo.create_playlist(user_id, name)
    
    # Add tracks
    for track_id in track_ids:
        await repo.add_track_to_playlist(playlist_id, track_id)
    
    return {
        "playlist_id": playlist_id,
        "name": name,
        "track_count": len(track_ids)
    }
```

---

## 📊 Updated State Schema

### New Fields in `AgentState`

```python
{
    # Existing fields...
    
    # NEW: Playlist analysis
    "playlist_profile": {
        "avg_bpm": float,
        "avg_energy": float,
        "top_genres": List[str],
        "description": str  # Natural language
    },
    
    # NEW: Reference track (from Step 2A)
    "reference_track": {
        "id": int,
        "artist": str,
        "bpm": float,
        "energy": float
    },
    
    # NEW: User focus preference (from Step 2B)
    "focus_preference": str,  # "vocal", "instrumental", "balanced"
    
    # NEW: Saved playlist info
    "saved_playlist": {
        "id": int,
        "name": str,
        "track_count": int
    }
}
```

### New Fields in `UIState`

```python
class ButtonOption(BaseModel):
    id: str
    label: str
    sublabel: Optional[str]  # NEW: Secondary description
    action: str
    payload: Dict[str, Any]
```

---

## 🎯 Success Metrics

### User Experience
- **Speed:** 3-4 clicks from start to save
- **Clarity:** User understands what agent is doing
- **Control:** User feels in control of the direction
- **Satisfaction:** Results feel personalized and relevant

### Technical
- **LLM Calls:** Max 5 per session (analysis, vibe descriptions, pitches, justification)
- **DB Queries:** Max 4 per session (centroid, search, reference tracks, save)
- **Response Time:** < 5 seconds per step

---

## 🚀 Implementation Phases

### Phase 1: Playlist Analysis (Week 1)
- [ ] Implement `analyze_playlist_vibe` tool
- [ ] Update Supervisor to call it first
- [ ] Generate natural language descriptions
- [ ] Create vibe selection UI options

### Phase 2: Smart Artist Knowledge (Week 2)
- [ ] Implement `get_reference_tracks` tool
- [ ] Generate vibe descriptions for reference tracks
- [ ] Update `check_knowledge` to use references
- [ ] Add fallback to simple focus question

### Phase 3: Save Playlist (Week 3)
- [ ] Implement `save_playlist` action
- [ ] Add "Find More" iteration logic
- [ ] Add "Start Over" reset logic
- [ ] Update presentation UI with new options

### Phase 4: Polish & Testing (Week 4)
- [ ] Add streaming for thought process
- [ ] Optimize LLM prompts
- [ ] Add error handling
- [ ] User testing & refinement

---

## 🎨 UI/UX Considerations

### Visual Hierarchy
1. **Agent Message** - Clear, conversational
2. **Analysis/Stats** - Compact, scannable
3. **Options** - Large, clickable buttons with icons
4. **Track Cards** - Rich with audio features

### Interaction Patterns
- **Loading States:** Show "Analyzing..." / "Searching..." / "Generating..."
- **Thought Process:** Stream supervisor reasoning in real-time
- **Animations:** Smooth transitions between steps
- **Feedback:** Immediate visual feedback on clicks

### Mobile Optimization
- Large touch targets (min 44px)
- Vertical scrolling for track cards
- Sticky save button at bottom
- Swipe gestures for track cards

---

## 🔮 Future Enhancements

### Advanced Features (Post-MVP)
1. **Multi-Playlist Analysis** - Combine multiple playlists
2. **Mood Slider** - Fine-tune energy/BPM ranges
3. **Genre Exploration** - "Show me more [genre]"
4. **Collaborative Filtering** - "Users like you also liked..."
5. **Temporal Preferences** - "Morning vibes" vs "Evening vibes"

### AI Improvements
1. **Learning from Saves** - Track which recommendations get saved
2. **Personalization** - Build user taste profile over time
3. **Contextual Awareness** - Time of day, weather, activity
4. **Multi-Modal** - Analyze album art, lyrics sentiment

---

## 📝 Open Questions

1. **Playlist Naming:** Auto-generate or ask user?
   - **Proposal:** Auto-generate with option to rename

2. **Track Limit:** Always 5 tracks or configurable?
   - **Proposal:** Start with 5, add "Find More" to get 5 more

3. **Reference Track Selection:** How to pick the best 3?
   - **Proposal:** Most recent + most played + random

4. **Vibe Description:** How detailed should it be?
   - **Proposal:** 1-2 sentences max, focus on feel not technical details

5. **Error Handling:** What if playlist has < 3 tracks?
   - **Proposal:** Show error message, suggest adding more tracks first

---

## 🎯 Definition of Done

### Step 1 Complete When:
- [x] Playlist analysis generates accurate stats
- [x] LLM produces natural language descriptions
- [x] Vibe options are contextualized to playlist
- [x] User can select a vibe and constraints are set

### Step 2 Complete When:
- [x] Agent detects known vs unknown artists
- [x] Reference tracks are fetched and described
- [x] Fallback question works when no known artists
- [x] User selection updates constraints

### Step 3 Complete When:
- [x] Final presentation shows 5 tracks
- [x] Justification explains reasoning clearly
- [x] Save playlist creates new playlist in DB
- [x] User can iterate or start over

### Overall Complete When:
- [x] Full flow works end-to-end
- [x] Average session is 3-4 clicks
- [x] User can save results
- [x] Agent feels intelligent and conversational
- [x] No infinite loops or errors
