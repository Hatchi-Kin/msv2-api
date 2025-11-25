"""Discovery Node - Phase 1: The Math.

Discovers candidate tracks based on vector similarity to playlist centroid.
"""

from typing import Dict, Any
import asyncpg

from api.agents.gem_hunter.state import AgentState, UIState
from api.repositories.library import LibraryRepository
from api.core.logger import logger


class DiscoveryNode:
    """Handles centroid calculation and candidate track discovery."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.repo = LibraryRepository(pool)

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Phase 1: The Math.
        Calculates centroid and finds hidden gems.
        """
        logger.info("--- Node: Discovery ---")
        playlist_id = state["playlist_id"]
        exclude_ids = state.get("excluded_ids", [])
        exclude_artists = state.get("excluded_artists", [])

        # 1. Calculate Centroid
        centroid = await self.repo.get_playlist_centroid(playlist_id)
        if not centroid:
            return {
                "next_step": "end",
                "ui_state": UIState(
                    message="Playlist is empty or has no vectors.", cards=[], options=[]
                ).model_dump(),
            }

        # 2. Search Hidden Gems (fetch more to account for filtering)
        candidates = await self.repo.search_hidden_gems(
            centroid,
            exclude_ids,
            exclude_artists,
            limit=15,  # Fetch more since we'll filter by artist knowledge
        )

        # Convert to dict for state
        candidate_dicts = [t[0].model_dump() for t in candidates]

        if not candidate_dicts:
            return {
                "next_step": "end",
                "ui_state": UIState(
                    message="No similar tracks found.", cards=[], options=[]
                ).model_dump(),
            }

        return {
            "centroid": centroid,
            "candidate_tracks": candidate_dicts,
            "enriched_tracks": [],  # Reset
            "next_step": "analysis",
        }
