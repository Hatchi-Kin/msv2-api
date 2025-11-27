"""Presentation Node - Phase 3: The Creative.

Generates personalized pitches and presents final recommendations.
"""

from typing import Dict, Any
import asyncpg

from api.agents.gem_hunter.state import AgentState, UIState, ButtonOption
from api.repositories.library import LibraryRepository
from api.agents.gem_hunter.llm_factory import get_llm
from api.agents.gem_hunter.exceptions import LLMFailureError
from api.core.logger import logger

# Import extracted logic
from api.agents.gem_hunter.core.vibe_matching import filter_by_vibe, generate_vibe_fun_fact
from api.agents.gem_hunter.core.track_formatting import create_track_cards
from api.agents.gem_hunter.llm.pitch_writer import generate_pitches
from api.agents.gem_hunter.llm.justification_generator import generate_justification


class PresentationNode:
    """Handles vibe selection, track filtering, and pitch generation."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.repo = LibraryRepository(pool)

        # Initialize LLM for creative generation
        try:
            from api.core.config import settings

            self.llm = get_llm(model=settings.LLM_CREATIVE_MODEL, temperature=0.7)
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise LLMFailureError(f"Could not initialize LLM: {e}")

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Phase 3: The Creative.
        Generates pitches and presents recommendations.
        """
        logger.info("--- Node: Presentation ---")
        tracks = state["enriched_tracks"]

        # --- VIBE CHECK ---
        if not state.get("vibe_checked"):
            fun_fact = generate_vibe_fun_fact(tracks)
            message = "I've analyzed the sonic profile of these tracks. How would you like me to shape the final selection?"

            return {
                "next_step": "end",
                "ui_state": UIState(
                    message=message,
                    fun_fact=fun_fact,
                    cards=[],
                    options=[
                        ButtonOption(
                            id="vibe_chill",
                            label="Chill & Relaxed",
                            action="set_vibe",
                            payload={"vibe": "Chill"},
                        ),
                        ButtonOption(
                            id="vibe_energy",
                            label="High Energy",
                            action="set_vibe",
                            payload={"vibe": "Energy"},
                        ),
                        ButtonOption(
                            id="vibe_surprise",
                            label="Surprise Me",
                            action="set_vibe",
                            payload={"vibe": "Surprise"},
                        ),
                    ],
                ).model_dump(),
            }

        # Filter based on vibe choice
        vibe_choice = state.get("vibe_choice", "Surprise")
        tracks = filter_by_vibe(tracks, vibe_choice)

        # --- PITCH GENERATION ---
        pitches = await generate_pitches(
            tracks, vibe_choice, state.get("user_preferences", "Unknown"), self.llm
        )

        # --- FINAL JUSTIFICATION ---
        # Get playlist context for better justification
        playlist_id = state.get("playlist_id")
        candidate_tracks = state.get("candidate_tracks", [])
        justification = await generate_justification(
            tracks, vibe_choice, playlist_id, candidate_tracks, self.llm
        )

        # Create UI State with full track cards
        cards = create_track_cards(tracks, pitches)

        # Construct backward-compatible message
        combined_message = (
            f"**PART 1 (Understanding):** {justification.understanding}\n\n"
            f"**PART 2 (Selection):** {justification.selection}"
        )

        ui_state = UIState(
            message=combined_message,
            understanding=justification.understanding,
            selection=justification.selection,
            cards=cards,
            options=[],  # No buttons needed - UI has its own add-to-playlist functionality
        )

        return {"ui_state": ui_state.model_dump(), "next_step": "end"}
