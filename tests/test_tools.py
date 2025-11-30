"""Unit tests for Tool Nodes v3."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.agents.gem_hunter.nodes.tools import ToolNodes
from api.agents.gem_hunter.state import AgentState


@pytest.fixture
def mock_pool():
    """Create mock database pool."""
    return AsyncMock()


@pytest.fixture
def tools(mock_pool):
    """Create ToolNodes instance with mocked LLMs."""
    with patch("api.agents.gem_hunter.nodes.tools.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        tools = ToolNodes(mock_pool)
        tools.creative_llm = mock_llm
        tools.reasoning_llm = mock_llm
        yield tools


@pytest.mark.asyncio
async def test_evaluate_results_sufficient(tools):
    """Test evaluate_results with sufficient candidates."""
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 1,
        "knowledge_checked": False,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
        "candidate_tracks": [
            {"id": str(i), "artist": f"Artist {i}", "distance": 0.2} for i in range(50)
        ],
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

    result = await tools.evaluate_results(state)

    assert result["quality_assessment"]["sufficient"] is True
    assert result["quality_assessment"]["quality_score"] > 0.6


@pytest.mark.asyncio
async def test_evaluate_results_insufficient(tools):
    """Test evaluate_results with insufficient candidates."""
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 1,
        "knowledge_checked": False,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
        "candidate_tracks": [],  # No candidates
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

    result = await tools.evaluate_results(state)

    assert result["quality_assessment"]["sufficient"] is False
    assert result["quality_assessment"]["quality_score"] == 0.0


@pytest.mark.asyncio
async def test_check_knowledge(tools):
    """Test check_knowledge extracts artists correctly."""
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 1,
        "knowledge_checked": False,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
        "candidate_tracks": [
            {"id": "1", "artist": "Artist A"},
            {"id": "2", "artist": "Artist B"},
            {"id": "3", "artist": "Artist A"},  # Duplicate
        ],
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

    result = await tools.check_knowledge(state)

    assert result["knowledge_checked"] is True
    options = result["ui_state"]["options"]
    # Should have unique artists + "None" + "All"
    assert len(options) == 4  # Artist A, Artist B, None, All


@pytest.mark.asyncio
async def test_present_results_with_unknown_artists(tools):
    """Test present_results prioritizes unknown artists."""
    # Mock LLM responses
    mock_response = MagicMock()
    mock_response.content = "Great track!"
    tools.creative_llm.ainvoke = AsyncMock(return_value=mock_response)
    tools.reasoning_llm.ainvoke = AsyncMock(return_value=mock_response)

    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 1,
        "knowledge_checked": True,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
        "candidate_tracks": [
            {
                "id": "1",
                "title": "Track 1",
                "artist": "Known Artist",
                "bpm": 120,
                "energy": 0.7,
            },
            {
                "id": "2",
                "title": "Track 2",
                "artist": "Unknown Artist",
                "bpm": 120,
                "energy": 0.7,
            },
            {
                "id": "3",
                "title": "Track 3",
                "artist": "Unknown Artist 2",
                "bpm": 120,
                "energy": 0.7,
            },
        ],
        "quality_assessment": {"sufficient": True},
        "known_artists": ["Known Artist"],
        "next_action": "",
        "supervisor_reasoning": "",
        "tool_parameters": {},
        "action_history": [],
        "iteration_count": 0,
        "ui_state": None,
        "error": None,
    }

    result = await tools.present_results(state)

    assert result["results_presented"] is True
    cards = result["ui_state"]["cards"]
    # Should prioritize unknown artists
    assert cards[0]["artist"] == "Unknown Artist"


@pytest.mark.asyncio
async def test_present_results_no_candidates(tools):
    """Test present_results handles no candidates gracefully."""
    state: AgentState = {
        "playlist_id": "123",
        "user_id": "user1",
        "playlist_analyzed": True,
        "vibe_choice": "similar",
        "search_iteration": 1,
        "knowledge_checked": True,
        "results_presented": False,
        "playlist_profile": {"avg_bpm": 120},
        "candidate_tracks": [],  # No candidates
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

    result = await tools.present_results(state)

    assert result["results_presented"] is True
    assert "couldn't find" in result["ui_state"]["message"].lower()
    assert len(result["ui_state"]["cards"]) == 0
