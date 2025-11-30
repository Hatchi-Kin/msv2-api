"""Supervisor Node - The brain that makes decisions."""

from typing import Literal, Dict, Any

from pydantic import BaseModel, Field

from api.agents.gem_hunter.state import AgentState
from api.agents.gem_hunter.llm_factory import get_llm
from api.core.config import settings
from api.core.logger import logger


class SupervisorDecision(BaseModel):
    """Structured output from supervisor LLM."""

    next_action: Literal[
        "analyze_playlist",
        "search_tracks",
        "evaluate_results",
        "check_knowledge",
        "present_results",
        "END",
    ]
    reasoning: str = Field(description="Why this action makes sense")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SupervisorNode:
    """The brain - decides what to do next."""

    def __init__(self):
        self.llm = get_llm(model=settings.LLM_REASONING_MODEL, temperature=0)

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Analyze state and decide next action."""
        logger.info("🧠 Supervisor thinking...")

        # Handle both dict and Pydantic model
        if isinstance(state, dict):
            state = AgentState(**state)

        # Safety: Max iterations
        iteration = state.iteration_count
        if iteration >= 10:
            logger.warning("⚠️ Max iterations reached, forcing END")
            return {
                "next_action": "present_results",
                "supervisor_reasoning": "Max iterations reached",
                "iteration_count": iteration + 1,
            }

        # Loop detection: Check last 3 actions
        history = state.action_history
        if len(history) >= 3 and len(set(history[-3:])) == 1:
            logger.warning(
                f"⚠️ Loop detected: {history[-3:]}. Forcing different action."
            )
            # Force present_results to break loop
            return {
                "next_action": "present_results",
                "supervisor_reasoning": "Loop detected, presenting results",
                "iteration_count": iteration + 1,
                "action_history": history + ["present_results"],
            }

        # Build context for LLM
        context = self._build_context(state)

        # Get decision from LLM
        try:
            decision = await self.llm.with_structured_output(
                SupervisorDecision
            ).ainvoke(context)
            logger.info(f"✅ Decision: {decision.next_action}")
            logger.info(f"   Reasoning: {decision.reasoning}")

            # Update action history
            new_history = (history + [decision.next_action])[-3:]  # Keep last 3

            return {
                "next_action": decision.next_action,
                "supervisor_reasoning": decision.reasoning,
                "tool_parameters": decision.parameters,
                "action_history": new_history,
                "iteration_count": iteration + 1,
            }

        except Exception as e:
            logger.error(f"❌ Supervisor LLM failed: {e}")
            return {
                "next_action": "present_results",
                "supervisor_reasoning": f"Error: {e}",
                "iteration_count": iteration + 1,
            }

    def _build_context(self, state: AgentState) -> str:
        """Build LLM prompt from current state."""

        # Handle both dict and Pydantic model
        if isinstance(state, dict):
            state = AgentState(**state)

        # Extract state
        playlist_analyzed = state.playlist_analyzed
        vibe = state.vibe_choice
        candidates = state.candidate_tracks
        quality = state.quality_assessment or {}
        knowledge_checked = state.knowledge_checked
        known_artists = state.known_artists
        iteration = state.iteration_count
        search_iter = state.search_iteration

        return f"""You are a music curator supervisor. Your mission: 
    create a 5-track playlist of hidden gems that matches user's taste and prioritizes tracks from artists user doesn't know.

Current State:
- Playlist analyzed: {playlist_analyzed}
- Vibe selected: {vibe or "Not yet"}
- Search iteration: {search_iter}
- Candidates found: {len(candidates)}
- Quality score: {quality.get('quality_score', 'Not evaluated')}
- Quality sufficient: {quality.get('sufficient', 'Not evaluated')}
- Knowledge checked: {knowledge_checked}
- Known artists: {len(known_artists)} ({', '.join(known_artists[:3])}{'...' if len(known_artists) > 3 else ''})
- Iteration: {iteration}/10

Available Tools:
1. analyze_playlist - Analyze source playlist, ask user for vibe (INTERRUPTS USER)
2. search_tracks - Search for similar tracks with constraints
3. evaluate_results - Assess quality/quantity of current candidates
4. check_knowledge - Ask which artists user knows in order to prioritize unknown tracks(INTERRUPTS USER)
5. present_results - Show final 5-track playlist (ENDS MISSION)

Decision Rules:
- You can only interrupt user TWICE total (analyze + check_knowledge)
- If playlist not analyzed → MUST call analyze_playlist
- If vibe selected but no candidates → MUST call search_tracks
- If candidates exist but not evaluated → SHOULD call evaluate_results
- If quality poor and search_iter < 3 → CAN call search_tracks again
- If quality good and knowledge not checked → MUST call check_knowledge
- If knowledge checked and 5+ unknown tracks → MUST call present_results
- If user knows all and search_iter == 1 → MUST call search_tracks with exclusions
- If user knows all and search_iter > 1 → MUST call present_results (give up gracefully)
- If stuck or iteration >= 10 → MUST call present_results

What should you do next?"""
