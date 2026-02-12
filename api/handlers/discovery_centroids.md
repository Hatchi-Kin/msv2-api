# Discovery Latent Navigation: Logic and Rationale

## 🧩 The Problem: Textual Ambiguity
Semantic search using CLAP (Text-to-Audio) is powerful but often hits a wall called **"Textural Dominance."** 
When a user searches for *"Jazzy Hip Hop,"* the model might return a Folk track because it captures the "Jazzy" texture (acoustic instruments) better than it captures the "Hip Hop" culture.

## ⚖️ The Solution: Consensus-Based Steering
To fix this, we implement **Latent Steering Sliders**. These allow the user to mathematically "nudge" the search query toward (or away from) certain musical "Anchors."

### 1. The Expert Supervision Principle
We do not trust CLAP alone to define musical genres. Instead, we use **OpenL3** (a dedicated musicology model) and **Human Metadata** (User Tags) to find the "Ground Truth."

**The Consensus Rule:**
A track is only used as a reference point (Anchor) if both signals agree:
*   **Signal A (Human):** The metadata tag `genre` explicitly matches the target.
*   **Signal B (AI):** OpenL3's top predictions specifically identify that genre.

By averaging the CLAP embeddings of these "High Consensus" tracks, we find the absolute North Star for that vibe within the CLAP space.

### 2. The Slider Math (Vector Arithmetic)
Each slider represents a **Polarity Vector** (a line in space).

*   **Positive Steering:** Adding a centroid vector to the query moves the result closer to that vibe.
*   **Negative Steering:** Subtracting a centroid vector removes that vibe's influence.

**Formula:**
`Refined_Vector = Base_Query_Vector + (Direction_Vector * Slider_Weight)`

---

## 🎚 The 4 Primary Steering Axes (Finalized Feb 12)

These axes are calculated as **Directional Vectors** between our pure consensus centroids.

| Axis | Calculation (Vector Math) | Effect on Discovery |
| :--- | :--- | :--- |
| **Digital vs. Organic** | `Electronic` - `Acoustic` | Shifts from live instruments (Jazz/Folk) to synthesized beats. |
| **Energy** | `Hip-Hop` - `Ambient` | Increases rhythmic density and "intensity" vs. calm/sparse textures. |
| **Urban Identity** | `Hip-Hop` - `Global` | Boosts the cultural signature of Rap/Hip-Hop (The "Jurassic 5" Nudge). |
| **Bass Culture** | `Reggae` - `Global` | Dials in the specific laid-back, bass-heavy signature of the Reggae collection. |

## 🚀 Navigation Math
The steering works by taking the user's initial `Text_Query_Vector` and adding the weighted steering vectors.

**Formula:**
`Refined_Vector = Text_Vector + (Axis_Vector * Slider_Value)`

Where `Slider_Value` ranges from `-1.0` to `+1.0`. 
Moving a slider to `+1.0` pulls the results 100% toward that specific "Truth Anchor."
