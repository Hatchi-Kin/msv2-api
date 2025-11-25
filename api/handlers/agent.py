from typing import Dict, Any, Optional
import asyncpg
from langgraph.checkpoint.memory import MemorySaver
from fastapi import HTTPException

from api.agents.gem_hunter.graph import build_agent_graph
from api.agents.gem_hunter.state import UIState
from api.agents.gem_hunter.exceptions import LLMFailureError
from api.core.logger import logger

# Global checkpointer for MVP (Single worker only)
checkpointer = MemorySaver()


async def start_recommendation_handler(
    playlist_id: int, pool: asyncpg.Pool
) -> Optional[UIState]:
    """
    Start the Hidden Gem Hunter agent for a playlist.
    """
    app = build_agent_graph(pool, checkpointer=checkpointer)

    # Config for this thread
    thread_id = f"playlist_{playlist_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Initial State
    initial_state = {
        "messages": [],
        "playlist_id": playlist_id,
        "user_preferences": "General Vibe",
        "excluded_ids": [],
        "centroid": None,
        "candidate_tracks": [],
        "enriched_tracks": [],
        "ui_state": None,
        "next_step": None,
        "knowledge_checked": False,
        "vibe_checked": False,
        "vibe_choice": None,
        "fun_fact_1": None,
        "fun_fact_2": None,
    }

    try:
        final_state = await app.ainvoke(initial_state, config=config)
        return final_state.get("ui_state")
    except LLMFailureError as e:
        logger.error(f"❌ LLM service unavailable: {e}")
        return UIState(
            message="Sorry, our AI service is currently unavailable. Please try again later.",
            cards=[],
            options=[],
        ).model_dump()
    except Exception as e:
        logger.error(f"❌ Agent start failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent start failed: {str(e)}")


async def resume_agent_handler(
    action: str, playlist_id: int, payload: Dict[str, Any], pool: asyncpg.Pool
) -> Optional[UIState]:
    """
    Resume the agent with a user action.
    """
    logger.info(
        f"🔵 Resume agent called: action={action}, playlist_id={playlist_id}, payload={payload}"
    )

    app = build_agent_graph(pool, checkpointer=checkpointer)
    thread_id = f"playlist_{playlist_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Handle Action
    if action == "add":
        track_id = payload.get("track_id")
        logger.info(f"➕ Action: add track {track_id} to playlist {playlist_id}")

        # Initialize repo
        from api.repositories.library import LibraryRepository

        repo = LibraryRepository(pool)

        # Add track to playlist
        try:
            await repo.add_track_to_playlist(playlist_id, track_id)
            logger.info(
                f"✅ Successfully added track {track_id} to playlist {playlist_id}"
            )

            # Return current state without resuming graph, but update message
            # We need to fetch the current state to return it, or just return a success message
            # For now, let's just return a success UI update or null to keep current state
            # Ideally we should update the UI to show "Added!"
            # But since the frontend handles the button state, we might just need to acknowledge
            return None
        except Exception as e:
            logger.error(f"Failed to add track: {e}")
            # Optionally return error UI
            return None

    elif action == "submit_knowledge":
        known_artists = payload.get("known_artists", [])
        logger.info(f"✋ Action: submit_knowledge, known_artists={known_artists}")
        await app.aupdate_state(
            config,
            {
                "knowledge_checked": True,
                "known_artists": known_artists,
                "next_step": "analysis",
            },
        )

    elif action == "mark_known":
        artist = payload.get("artist")
        logger.info(f"✋ Action: mark_known for artist={artist}")
        await app.aupdate_state(
            config, {"knowledge_checked": True, "next_step": "analysis"}
        )

    elif action == "continue":
        logger.info("➡️ Action: continue (user doesn't know any artists)")
        await app.aupdate_state(
            config, {"knowledge_checked": True, "next_step": "analysis"}
        )

    elif action == "set_vibe":
        vibe = payload.get("vibe")
        logger.info(f"🎵 Action: set_vibe to {vibe}")
        await app.aupdate_state(
            config, {"vibe_checked": True, "vibe_choice": vibe, "next_step": "presentation"}
        )

    # Resume execution
    logger.info("🚀 Resuming graph execution...")
    try:
        final_state = await app.ainvoke(None, config=config)
        ui_state = final_state.get("ui_state")
        logger.info(f"📤 Returning ui_state: {ui_state}")
        return ui_state
    except LLMFailureError as e:
        logger.error(f"❌ LLM service unavailable: {e}")
        return UIState(
            message="Sorry, our AI service is currently unavailable. Please try again later.",
            cards=[],
            options=[],
        ).model_dump()
    except Exception as e:
        logger.error(f"❌ Graph execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
