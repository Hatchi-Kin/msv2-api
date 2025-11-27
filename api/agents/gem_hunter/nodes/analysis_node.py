"""Analysis Node - Phase 2: The Logic.

Analyzes playlist, filters candidates, and enriches metadata.
"""

from typing import Dict, Any
import asyncpg

from api.agents.gem_hunter.state import AgentState, UIState, ButtonOption
from api.repositories.library import LibraryRepository
from api.agents.gem_hunter.llm_factory import get_llm
from api.agents.gem_hunter.exceptions import LLMFailureError
from api.core.logger import logger

# Import extracted logic
from api.agents.gem_hunter.core.playlist_profiling import build_playlist_profile
from api.agents.gem_hunter.core.preference_filtering import (
    filter_by_known_artists,
    get_unique_artists,
)
from api.agents.gem_hunter.core.metadata_enrichment import enrich_tracks_parallel
from api.agents.gem_hunter.llm.playlist_analyzer import generate_playlist_analysis
from api.agents.gem_hunter.tools.enrichment import enrich_track_metadata


class AnalysisNode:
    """Handles playlist analysis, filtering, and metadata enrichment."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.repo = LibraryRepository(pool)

        # Initialize LLM for playlist analysis
        try:
            from api.core.config import settings

            self.llm = get_llm(model=settings.LLM_REASONING_MODEL, temperature=0)
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise LLMFailureError(f"Could not initialize LLM: {e}")

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Phase 2: The Logic.
        Analyzes playlist, filters candidates, and enriches metadata.
        """
        logger.info("--- Node: Analysis ---")
        candidates = state["candidate_tracks"]
        enriched = state.get("enriched_tracks", [])

        # If we have already enriched everything, move to presentation
        if len(enriched) == len(candidates):
            return {"next_step": "presentation"}

        # --- PLAYLIST ANALYSIS & KNOWLEDGE CHECK ---
        if not state.get("knowledge_checked"):
            # Get unique artists from candidates for investigation
            unique_artists = get_unique_artists(candidates, limit=5)

            # Generate playlist analysis if not already done
            if not state.get("playlist_analysis"):
                playlist_id = state.get("playlist_id")

                # Sample playlist tracks for analysis
                sampled_tracks = await self.repo.get_playlist_sample(
                    playlist_id, max_tracks=10
                )

                # Build playlist profile (pure function)
                profile = build_playlist_profile(sampled_tracks)

                # Generate LLM analysis
                analysis = await generate_playlist_analysis(profile, self.llm)

                # Create contextual message
                message = f"""{analysis}

To find hidden gems that match this vibe, I'm planning to investigate tracks similar to: {', '.join(unique_artists)}.

Do you already know any of these artists well? (I'll exclude them from recommendations)"""

                return {
                    "next_step": "end",  # Pause for user
                    "playlist_analysis": analysis,
                    "ui_state": UIState(
                        message=message,
                        cards=[],
                        options=[
                            ButtonOption(
                                id="submit_knowledge",
                                label="Continue",
                                action="submit_knowledge",
                                payload={"artists": unique_artists},
                            )
                        ],
                    ).model_dump(),
                }

        # --- FILTERING ---
        known_artists = state.get("known_artists", [])
        if known_artists and not state.get("excluded_artists"):
            # First time filtering - save to excluded_artists for future discovery calls
            state["excluded_artists"] = known_artists

        if known_artists:
            original_count = len(candidates)
            candidates = filter_by_known_artists(candidates, known_artists)
            filtered_count = len(candidates)
            if original_count != filtered_count:
                logger.info(
                    f"Filtered out {original_count - filtered_count} tracks by known artists: {known_artists}"
                )
                # Update state with filtered candidates
                state["candidate_tracks"] = candidates

        # Check if we have enough candidates after filtering
        MIN_CANDIDATES = 3
        if len(candidates) < MIN_CANDIDATES:
            # Not enough candidates - loop back to discovery to get more
            # Add current candidate IDs to exclusion list
            current_ids = [c["id"] for c in candidates]
            existing_excluded = state.get("excluded_ids", [])
            state["excluded_ids"] = list(set(existing_excluded + current_ids))

            logger.info(
                f"Only {len(candidates)} candidates left after filtering. Looping back to discovery for more..."
            )
            return {
                "excluded_ids": state["excluded_ids"],
                "excluded_artists": state.get("excluded_artists", []),
                "next_step": "discovery",  # Loop back to get more candidates
            }

        # --- BATCH ENRICHMENT (PARALLEL) ---
        # Process all tracks in parallel instead of one-by-one for massive speedup
        if not enriched:  # Only run once
            # Log stats
            all_genres = [
                t.get("genre") or t.get("top_5_genres", "").split(",")[0].strip()
                for t in candidates
                if t.get("genre") or t.get("top_5_genres")
            ]
            unique_genres = list(set(g for g in all_genres if g))[:3]
            logger.info(
                f"🎵 Enriching {len(candidates)} tracks in parallel across {len(unique_genres)} genres."
            )

            # Enrich all tracks in parallel using extracted function
            enriched_tracks = await enrich_tracks_parallel(
                candidates, enrich_track_metadata, self.repo
            )

            # Move to presentation
            return {"enriched_tracks": enriched_tracks, "next_step": "presentation"}

        # If we already have enriched tracks, move to presentation
        return {"next_step": "presentation"}
