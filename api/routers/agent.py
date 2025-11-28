from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends

from api.core.dependencies import get_db_pool, LibraryRepo, CurrentUser
from api.agents.gem_hunter.state import UIState
from api.handlers.agent import start_recommendation_handler, resume_agent_handler
from api.models.agent import ResumeAgentRequest

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
    request: ResumeAgentRequest,
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Resume the agent with a user action (e.g. add track)."""
    # Ensure track_id is in payload if provided at top level
    if request.track_id is not None:
        request.payload["track_id"] = request.track_id

    return await resume_agent_handler(
        request.action, request.playlist_id, request.payload, pool, library_repo
    )
