from typing import Optional, Dict, Any

import asyncpg
from fastapi import APIRouter, Depends

from api.core.dependencies import get_db_pool, LibraryRepo, CurrentUser
from api.agents.gem_hunter.state import UIState
from api.handlers.agent import start_recommendation_handler, resume_agent_handler

agent_router = APIRouter(prefix="/agent", tags=["agent"])


@agent_router.post("/recommend/{playlist_id}", response_model=Optional[UIState])
async def recommend_hidden_gems(
    _user: CurrentUser, playlist_id: int, pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Start the Hidden Gem Hunter agent for a playlist."""
    return await start_recommendation_handler(playlist_id, pool)


@agent_router.post("/resume", response_model=Optional[UIState])
async def resume_agent(
    library_repo: LibraryRepo,
    _user: CurrentUser,
    action: str,
    track_id: Optional[int],
    playlist_id: int,
    payload: Dict[str, Any],
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Resume the agent with a user action (e.g. add track)."""
    return await resume_agent_handler(action, playlist_id, payload, pool, library_repo)
