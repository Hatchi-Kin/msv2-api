from typing import Optional, Dict, Any

import asyncpg
from fastapi import APIRouter, Depends, Body

from api.core.dependencies import get_db_pool
from api.agents.gem_hunter.state import UIState
from api.handlers.agent import start_recommendation_handler, resume_agent_handler

agent_router = APIRouter(prefix="/agent", tags=["agent"])


@agent_router.post("/recommend/{playlist_id}", response_model=Optional[UIState])
async def recommend_hidden_gems(
    playlist_id: int, pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Start the Hidden Gem Hunter agent for a playlist."""
    return await start_recommendation_handler(playlist_id, pool)


@agent_router.post("/resume", response_model=Optional[UIState])
async def resume_agent(
    action: str = Body(..., embed=True),
    track_id: Optional[int] = Body(None, embed=True),
    playlist_id: int = Body(..., embed=True),
    payload: Dict[str, Any] = Body({}, embed=True),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Resume the agent with a user action (e.g. add track)."""
    return await resume_agent_handler(action, playlist_id, payload, pool)
