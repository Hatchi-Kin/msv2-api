from typing import Dict, Any, Optional

import asyncpg
from langgraph.checkpoint.memory import MemorySaver
from fastapi import HTTPException

from api.agents.gem_hunter.graph import build_agent_graph
from api.agents.gem_hunter.state import AgentState
from api.agents.gem_hunter.exceptions import LLMFailureError
from api.repositories.library import LibraryRepository
from api.core.logger import logger

# Global checkpointer for MVP (Single worker only)
checkpointer = MemorySaver()


async def start_recommendation_handler(
    playlist_id: int, pool: asyncpg.Pool
) -> Optional[Dict[str, Any]]:
    """Start the Hidden Gem Hunter agent from a playlist (v3 supervisor pattern)."""
    app = build_agent_graph(pool, checkpointer=checkpointer)

    # Config for this thread
    thread_id = f"playlist_{playlist_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Initial State (v3)
    initial_state: AgentState = {
        "playlist_id": str(playlist_id),
        "user_id": "default",  # TODO: Get from auth
        "playlist_analyzed": False,
        "vibe_choice": None,
        "search_iteration": 0,
        "knowledge_checked": False,
        "results_presented": False,
        "playlist_profile": None,
        "candidate_tracks": [],
        "quality_assessment": None,
        "known_artists": [],
        "next_action": "",
        "supervisor_reasoning": "",
        "tool_parameters": {},
        "action_history": [],
        "iteration_count": 0,
        "ui_state": None,
        "error": None,
    }

    try:
        logger.info(f"🚀 Starting agent for playlist {playlist_id}")
        final_state = await app.ainvoke(initial_state, config=config)
        return final_state.get("ui_state")
    except LLMFailureError as e:
        logger.error(f"❌ LLM service unavailable: {e}")
        return {
            "message": "Sorry, our AI service is currently unavailable. Please try again later.",
            "cards": [],
            "options": [],
        }
    except Exception as e:
        logger.error(f"❌ Agent start failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent start failed: {str(e)}")


async def resume_agent_handler(
    action: str,
    playlist_id: int,
    payload: Dict[str, Any],
    pool: asyncpg.Pool,
    library_repo: LibraryRepository,
) -> Optional[Dict[str, Any]]:
    """Resume the agent with a user action (v3 supervisor pattern)."""
    logger.info(f"🔵 Resume agent: action={action}, playlist_id={playlist_id}")

    app = build_agent_graph(pool, checkpointer=checkpointer)
    thread_id = f"playlist_{playlist_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Handle Action
    if action == "add":
        track_id = payload.get("track_id")  # payload is a dict, not Pydantic
        logger.info(f"➕ Action: add track {track_id} to playlist {playlist_id}")

        try:
            await library_repo.add_track_to_playlist(playlist_id, track_id)
            logger.info(
                f"✅ Successfully added track {track_id} to playlist {playlist_id}"
            )
            return None  # Frontend handles UI update
        except Exception as e:
            logger.error(f"Failed to add track: {e}")
            return None

    elif action == "set_vibe":
        # User selected vibe after analyze_playlist
        vibe = payload.get("vibe")  # payload is a dict, not Pydantic
        logger.info(f"🎵 Action: set_vibe to {vibe}")

        await app.aupdate_state(config, {"vibe_choice": vibe})

    elif action == "submit_knowledge":
        # User selected known artists after check_knowledge
        known_artists = payload.get(
            "known_artists", []
        )  # payload is a dict, not Pydantic
        logger.info(f"✋ Action: submit_knowledge, known_artists={known_artists}")

        # Handle special values
        if known_artists == ["none"]:
            known_artists = []
        elif known_artists == ["all"]:
            # Get all artists from candidates
            state = await app.aget_state(config)
            candidates = state.values.get("candidate_tracks", [])
            known_artists = list(
                set(
                    t.get("artist") if isinstance(t, dict) else t.artist
                    for t in candidates[:20]
                )
            )

        await app.aupdate_state(config, {"known_artists": known_artists})

    else:
        logger.warning(f"⚠️ Unknown action: {action}")
        return None

    # Resume execution
    logger.info("🚀 Resuming graph execution...")
    try:
        final_state = await app.ainvoke(None, config=config)
        ui_state = final_state.get("ui_state")
        return ui_state
    except LLMFailureError as e:
        logger.error(f"❌ LLM service unavailable: {e}")
        return {
            "message": "Sorry, our AI service is currently unavailable. Please try again later.",
            "cards": [],
            "options": [],
        }
    except Exception as e:
        logger.error(f"❌ Graph execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
