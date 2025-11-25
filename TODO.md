# Future Improvements & Ideas

## Feature: Artist Centroids / Profiling

**Concept**: 
Precompute and store the "centroid" (average vector) for every artist in the database. This would likely require a new `artists` table or a materialized view.

**Why?**
1.  **Efficiency**: Searching against ~5,000 artists is orders of magnitude faster than searching ~100,000 tracks.
2.  **"Vibe Match"**: Enables queries like "Find me artists that sound like this playlist" or "Find artists similar to this artist" (using their actual audio content, not just metadata tags).
3.  **Hierarchical Search**: 
    -   Step 1: Find top 10 artists matching a query vector.
    -   Step 2: Search only the tracks belonging to those artists.
    -   *Benefit*: Filters out random matches from unrelated genres/artists, potentially improving recommendation quality.

**Implementation Notes**:
-   **Calculation**: `AVG(embedding_512_vector)` for all tracks by `artist_folder`.
-   **Normalization**: Ensure the resulting centroid is normalized.
-   **Caveat**: "Diverse" artists (e.g., Queen, Bowie) might have a "muddy" average that sits in the middle of nowhere. This is usually acceptable for high-level discovery, but "Multi-Centroid" (clustering per artist) is a fancy upgrade path.



## improve agent for prod

### Global checkpointer for MVP (Single worker only)
checkpointer = MemorySaver()
need to add real postgreSQL
