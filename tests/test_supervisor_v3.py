"""Unit tests for Supervisor Node v3."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.agents.gem_hunter.nodes.supervisor_v3 import SupervisorNode, SupervisorDecision
from api.agents.gem_hunter.state_v3 import AgentState


@pytest.fixture
def supervisor():
    """Create supervisor instance with mocked LLM."""
    with patch('api.agents.gem_hunter.nodes.supervisor_v3.get_llm') as mock_get_llm:
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        supervisor = SupervisorNode()
        supervisor.llm = mock_llm
        yield supervisor


@pytest.mark.asyncio
async def test_supervisor_initial_state(supervisor):
    """Test supervisor decides to analyze_playlist when nothing is done."""
    # Mock LLM response
    mock_decision = SupervisorDecision(
        next_action="analyze_playlist",
        reasoning="Playlist not analyzed yet",
        parameters={}
    )
    
    mock_structured = AsyncMock()
    mock_structured.ainvoke = AsyncMock(return_value=mock_decision)
    supervisor.llm.with_structured_output = MagicMock(return_value=mock_structured)
    
    # Initial state
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
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
    
    result = await supervisor.execute(state)
    
    assert result["next_action"] == "analyze_playlist"
    assert result["iteration_count"] == 1
    assert "analyze_playlist" in result["action_history"]


@pytest.mark.asyncio
async def test_supervisor_max_iterations(supervisor):
    """Test supervisor forces END when max iterations reached."""
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 1,
        "knowledge_checked": False,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
        "candidate_tracks": [],
        "quality_assessment": None,
        "known_artists": [],
        "next_action": "",
        "supervisor_reasoning": "",
        "tool_parameters": {},
        "action_history": [],
        "iteration_count": 10,  # Max reached
        "ui_state": None,
        "error": None,
    }
    
    result = await supervisor.execute(state)
    
    assert result["next_action"] == "present_results"
    assert result["supervisor_reasoning"] == "Max iterations reached"
    assert result["iteration_count"] == 11


@pytest.mark.asyncio
async def test_supervisor_loop_detection(supervisor):
    """Test supervisor detects and breaks loops."""
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 1,
        "knowledge_checked": False,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
        "candidate_tracks": [],
        "quality_assessment": None,
        "known_artists": [],
        "next_action": "",
        "supervisor_reasoning": "",
        "tool_parameters": {},
        "action_history": ["search_tracks", "search_tracks", "search_tracks"],  # Loop!
        "iteration_count": 5,
        "ui_state": None,
        "error": None,
    }
    
    result = await supervisor.execute(state)
    
    assert result["next_action"] == "present_results"
    assert "Loop detected" in result["supervisor_reasoning"]
    assert "present_results" in result["action_history"]


@pytest.mark.asyncio
async def test_supervisor_llm_failure(supervisor):
    """Test supervisor handles LLM failures gracefully."""
    # Mock LLM to raise exception
    mock_structured = AsyncMock()
    mock_structured.ainvoke = AsyncMock(side_effect=Exception("LLM service down"))
    supervisor.llm.with_structured_output = MagicMock(return_value=mock_structured)
    
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 1,
        "knowledge_checked": False,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
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
    
    result = await supervisor.execute(state)
    
    assert result["next_action"] == "present_results"
    assert "Error" in result["supervisor_reasoning"]


@pytest.mark.asyncio
async def test_supervisor_action_history_tracking(supervisor):
    """Test supervisor correctly tracks action history."""
    mock_decision = SupervisorDecision(
        next_action="search_tracks",
        reasoning="Need to search",
        parameters={}
    )
    
    mock_structured = AsyncMock()
    mock_structured.ainvoke = AsyncMock(return_value=mock_decision)
    supervisor.llm.with_structured_output = MagicMock(return_value=mock_structured)
    
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 0,
        "knowledge_checked": False,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
        "candidate_tracks": [],
        "quality_assessment": None,
        "known_artists": [],
        "next_action": "",
        "supervisor_reasoning": "",
        "tool_parameters": {},
        "action_history": ["analyze_playlist", "evaluate_results"],
        "iteration_count": 2,
        "ui_state": None,
        "error": None,
    }
    
    result = await supervisor.execute(state)
    
    # Should keep last 3 actions
    assert len(result["action_history"]) == 3
    assert result["action_history"] == ["analyze_playlist", "evaluate_results", "search_tracks"]
