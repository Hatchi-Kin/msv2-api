# For local development
## you might port-forward the k3s postgres services:
```sh
kubectl port-forward service/postgres-service 5432:5432 -n glasgow-prod
```
and
```sh
kubectl port-forward -n glasgow-prod svc/minio-service 9000:9000
```

# or maybe just port forward the prod api directly
```sh
kubectl port-forward -n glasgow-prod svc/fastapi-msv2-api-service 8000:8010
```


# Then start the app
```sh
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```


# Hidden Gem Hunter Agent Analysis

## Architecture Overview

The **Hidden Gem Hunter** is a LangGraph-based agent designed to find "hidden gems" (tracks similar to a user's playlist but from artists they likely don't know) in a music library.

It operates in three distinct phases, modeled as graph nodes:

1.  **Discovery (The Math)**: Vector-based retrieval.
2.  **Analysis (The Logic)**: Filtering, knowledge checking, and metadata enrichment.
3.  **Presentation (The Creative)**: Vibe selection, pitch generation, and final justification.

### Agent Flow

```mermaid
graph TD
    Start([Start]) --> Discovery
    
    subgraph "Phase 1: Discovery"
        Discovery[Discovery Node<br/>(Vector Search)]
    end
    
    Discovery --> CheckDiscovery{Found<br/>Candidates?}
    CheckDiscovery -- No --> End([End])
    CheckDiscovery -- Yes --> Analysis
    
    subgraph "Phase 2: Analysis"
        Analysis[Analysis Node<br/>(Filter & Enrich)]
        Analysis --> CheckAnalysis{Next Step?}
        
        CheckAnalysis -- "Knowledge Check<br/>(User Input)" --> End
        CheckAnalysis -- "Not Enough<br/>Candidates" --> Discovery
        CheckAnalysis -- "Ready" --> Presentation
    end
    
    subgraph "Phase 3: Presentation"
        Presentation[Presentation Node<br/>(Vibe & Pitch)]
        Presentation --> CheckPresentation{Next Step?}
        
        CheckPresentation -- "Vibe Check<br/>(User Input)" --> End
        CheckPresentation -- "Final Result" --> End
    end
    
    style Discovery fill:#e1f5fe,stroke:#01579b
    style Analysis fill:#fff3e0,stroke:#e65100
    style Presentation fill:#f3e5f5,stroke:#4a148c
```

## Detailed Component Logic

### 1. Discovery Node (`discovery_node.py`)
-   **Input**: `playlist_id`
-   **Action**:
    -   Calculates the **Centroid** (average vector) of the user's playlist.
    -   Performs a **Vector Search** to find tracks closest to this centroid.
    -   **Excludes** tracks already in the playlist.
-   **Output**: List of `candidate_tracks` (raw DB records).

### 2. Analysis Node (`analysis_node.py`)
-   **Input**: `candidate_tracks`
-   **Action**:
    -   **Knowledge Check**: Identifies unique artists and asks the user: *"Do you know these?"* (Uses LLM to analyze playlist vibe first).
    -   **Filtering**: Removes tracks by artists the user explicitly knows.
    -   **Loop Back**: If filtering leaves < 3 candidates, it loops back to **Discovery** to fetch more, adding current candidates to an exclusion list.
    -   **Enrichment**: Fetches metadata (genres, audio features) from Spotify in parallel.
-   **Output**: `enriched_tracks` or a loop command.

### 3. Presentation Node (`presentation_node.py`)
-   **Input**: `enriched_tracks`
-   **Action**:
    -   **Vibe Check**: Asks the user to refine the selection (e.g., "Chill", "Energy", "Surprise").
    -   **Filtering**: Filters the enriched list based on the selected vibe.
    -   **Creative Generation**:
        -   **Pitches**: LLM writes a persuasive "pitch" for each track.
        -   **Justification**: LLM explains *why* these tracks fit the playlist and vibe.
-   **Output**: Final `UIState` with track cards.

---
