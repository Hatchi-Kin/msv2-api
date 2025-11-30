# Music Curator Agent v3 - Frontend Integration Guide

**For React Developers**

## Overview

The Music Curator Agent v3 is a conversational AI that curates personalized playlists. It uses a supervisor pattern to make intelligent decisions and only interrupts the user **twice** (vibe selection + artist knowledge).

## API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. Start Agent

**Endpoint:** `POST /agent/recommend/{playlist_id}`

**Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Response:**
```json
{
  "message": "I analyzed your playlist.\n\n📊 BPM: 120, Energy: 0.13\n\n💭 This playlist exudes a mellow, laid-back jazz atmosphere...\n\nWhat vibe should I explore?",
  "options": [
    {"label": "🔥 More of this", "value": "similar"},
    {"label": "😌 Chill", "value": "chill"},
    {"label": "⚡ Energy", "value": "energy"},
    {"label": "🌟 Surprise", "value": "surprise"}
  ],
  "cards": []
}
```

### 2. Resume Agent (User Action)

**Endpoint:** `POST /agent/resume`

**Request Body:**
```json
{
  "action": "set_vibe" | "submit_knowledge" | "add",
  "playlist_id": 123,
  "payload": {
    // Action-specific data
  }
}
```

**Response:** Same format as start (UIState)

---

## User Flow

### Step 1: Analyze Playlist (Automatic)

Agent analyzes the playlist and returns vibe options.

**UI State:**
```json
{
  "message": "I analyzed your playlist...",
  "options": [
    {"label": "🔥 More of this", "value": "similar"},
    {"label": "😌 Chill", "value": "chill"},
    {"label": "⚡ Energy", "value": "energy"},
    {"label": "🌟 Surprise", "value": "surprise"}
  ],
  "cards": []
}
```

**Frontend Action:**
- Display the message
- Render 4 buttons from `options`
- On click, call resume with `action: "set_vibe"`

**Example:**
```typescript
const handleVibeSelect = async (vibe: string) => {
  const response = await fetch('/agent/resume', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'set_vibe',
      playlist_id: playlistId,
      payload: { vibe }
    })
  });
  
  const uiState = await response.json();
  setUIState(uiState);
};
```

---

### Step 2: Artist Knowledge Check (Automatic)

After searching, agent asks which artists the user knows.

**UI State:**
```json
{
  "message": "Which of these artists do you know? (Select all that apply)",
  "options": [
    {"label": "Patrice", "value": "Patrice"},
    {"label": "Feist", "value": "Feist"},
    {"label": "Alice Russell", "value": "Alice Russell"},
    // ... more artists
    {"label": "None of them", "value": "none"},
    {"label": "All of them", "value": "all"}
  ],
  "cards": []
}
```

**Frontend Action:**
- Display the message
- Render checkboxes for each artist
- Add "Submit" button
- On submit, call resume with `action: "submit_knowledge"`

**Example:**
```typescript
const handleKnowledgeSubmit = async (selectedArtists: string[]) => {
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
  setUIState(uiState);
};
```

**Special Values:**
- `["none"]` - User knows none of the artists
- `["all"]` - User knows all of the artists (agent will re-search)

---

### Step 3: Final Results (Automatic)

Agent presents 5 curated tracks with evidence-based justifications.

**UI State:**
```json
{
  "message": "Here are 5 hidden gems I curated for you!\n\nI selected these tracks to complement your playlist's intimate, low-energy character...",
  "options": [],
  "cards": [
    {
      "id": "3364",
      "title": "La Lluvia",
      "artist": "Nickodemus",
      "reason": "With its 143 BPM providing gentle momentum against your playlist's 120 BPM baseline, this track's remarkably low energy (0.23 vs 0.70) and warm tonal character (2532 vs 1706 brightness) create an intimate sonic landscape..."
    },
    // ... 4 more tracks
  ]
}
```

**Frontend Action:**
- Display the message (overall justification)
- Render track cards with:
  - Track title
  - Artist name
  - Reason (evidence-based justification)
  - Play button (if preview available)
  - Add to playlist button

**Example:**
```typescript
const TrackCard = ({ card }: { card: Card }) => (
  <div className="track-card">
    <h3>{card.title}</h3>
    <p className="artist">{card.artist}</p>
    <p className="reason">{card.reason}</p>
    <div className="actions">
      <button onClick={() => playTrack(card.id)}>▶️ Play</button>
      <button onClick={() => addToPlaylist(card.id)}>➕ Add</button>
    </div>
  </div>
);
```

---

## TypeScript Types

```typescript
interface UIState {
  message: string;
  options: Option[];
  cards: Card[];
}

interface Option {
  label: string;
  value: string;
}

interface Card {
  id: string;
  title: string;
  artist: string;
  reason: string;
}

interface ResumeRequest {
  action: 'set_vibe' | 'submit_knowledge' | 'add';
  playlist_id: number;
  payload: Record<string, any>;
}
```

---

## Complete React Component Example

```typescript
import { useState } from 'react';

interface UIState {
  message: string;
  options: Array<{label: string; value: string}>;
  cards: Array<{id: string; title: string; artist: string; reason: string}>;
}

export const MusicCuratorAgent = ({ playlistId, token }: Props) => {
  const [uiState, setUIState] = useState<UIState | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedArtists, setSelectedArtists] = useState<string[]>([]);

  // Start the agent
  const startAgent = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/agent/recommend/${playlistId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      setUIState(data);
    } catch (error) {
      console.error('Failed to start agent:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle vibe selection
  const handleVibeSelect = async (vibe: string) => {
    setLoading(true);
    try {
      const response = await fetch('/agent/resume', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: 'set_vibe',
          playlist_id: playlistId,
          payload: { vibe }
        })
      });
      const data = await response.json();
      setUIState(data);
    } catch (error) {
      console.error('Failed to set vibe:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle artist knowledge submission
  const handleKnowledgeSubmit = async () => {
    setLoading(true);
    try {
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
      const data = await response.json();
      setUIState(data);
      setSelectedArtists([]);
    } catch (error) {
      console.error('Failed to submit knowledge:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle add track to playlist
  const handleAddTrack = async (trackId: string) => {
    try {
      await fetch('/agent/resume', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: 'add',
          playlist_id: playlistId,
          payload: { track_id: trackId }
        })
      });
      alert('Track added!');
    } catch (error) {
      console.error('Failed to add track:', error);
    }
  };

  // Render based on UI state
  if (!uiState) {
    return (
      <button onClick={startAgent} disabled={loading}>
        {loading ? 'Starting...' : 'Find Hidden Gems'}
      </button>
    );
  }

  return (
    <div className="music-curator-agent">
      {/* Message */}
      <div className="message">
        {uiState.message.split('\n').map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>

      {/* Options (Vibe selection or Artist knowledge) */}
      {uiState.options.length > 0 && uiState.cards.length === 0 && (
        <div className="options">
          {/* Check if it's artist knowledge (has "None" and "All") */}
          {uiState.options.some(opt => opt.value === 'none') ? (
            // Artist knowledge checkboxes
            <>
              {uiState.options
                .filter(opt => opt.value !== 'none' && opt.value !== 'all')
                .map(option => (
                  <label key={option.value}>
                    <input
                      type="checkbox"
                      checked={selectedArtists.includes(option.value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedArtists([...selectedArtists, option.value]);
                        } else {
                          setSelectedArtists(selectedArtists.filter(a => a !== option.value));
                        }
                      }}
                    />
                    {option.label}
                  </label>
                ))}
              <button onClick={handleKnowledgeSubmit} disabled={loading}>
                {loading ? 'Submitting...' : 'Submit'}
              </button>
              <button onClick={() => handleKnowledgeSubmit()} disabled={loading}>
                None of them
              </button>
            </>
          ) : (
            // Vibe selection buttons
            uiState.options.map(option => (
              <button
                key={option.value}
                onClick={() => handleVibeSelect(option.value)}
                disabled={loading}
              >
                {option.label}
              </button>
            ))
          )}
        </div>
      )}

      {/* Track Cards (Final results) */}
      {uiState.cards.length > 0 && (
        <div className="track-cards">
          {uiState.cards.map(card => (
            <div key={card.id} className="track-card">
              <h3>{card.title}</h3>
              <p className="artist">{card.artist}</p>
              <p className="reason">{card.reason}</p>
              <button onClick={() => handleAddTrack(card.id)}>
                ➕ Add to Playlist
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Loading indicator */}
      {loading && <div className="loading">Processing...</div>}
    </div>
  );
};
```

---

## Styling Recommendations

```css
.music-curator-agent {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.message {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.options button {
  padding: 15px;
  font-size: 16px;
  border: 2px solid #007bff;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.options button:hover {
  background: #007bff;
  color: white;
}

.track-cards {
  display: grid;
  gap: 20px;
}

.track-card {
  border: 1px solid #ddd;
  padding: 20px;
  border-radius: 8px;
  background: white;
}

.track-card h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
}

.track-card .artist {
  color: #666;
  margin: 0 0 15px 0;
}

.track-card .reason {
  line-height: 1.6;
  margin-bottom: 15px;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}
```

---

## Error Handling

```typescript
try {
  const response = await fetch('/agent/resume', { /* ... */ });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  const data = await response.json();
  
  // Check for error in response
  if (data.message && data.message.includes('error')) {
    alert('Agent encountered an issue. Please try again.');
  }
  
  setUIState(data);
} catch (error) {
  console.error('API Error:', error);
  alert('Failed to communicate with agent. Please try again.');
}
```

---

## Key Points

1. **Only 2 User Interrupts**: Vibe selection → Artist knowledge → Results
2. **Evidence-Based Justifications**: Each track includes specific metrics (BPM, energy, brightness) compared to the playlist
3. **Automatic Flow**: Agent decides everything else (search, evaluate, present)
4. **Graceful Errors**: Agent handles failures and presents clear messages
5. **No Polling**: Agent uses interrupts, not polling

---

## Testing

Use the manual test script to see the full flow:
```bash
python tests/manual_agent_test_v3.py
```

This shows exactly what the frontend will receive at each step.

---

## Questions?

Check the full documentation:
- `AGENT_DOCUMENTATION_V3.md` - Complete technical docs
- `README_V3.md` - Quick start guide
- `MIGRATION_V2_TO_V3.md` - If migrating from v2

---

**Last Updated:** 2025-11-30  
**Version:** 3.0  
**Status:** ✅ Production Ready
