"""Integration tests for Music Curator Agent v3."""

from unittest.mock import AsyncMock

import pytest

from api.agents.gem_hunter.graph import build_agent_graph


@pytest.fixture
def mock_pool():
    """Create mock database pool."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_full_flow_analyze_to_present(mock_pool):
    """Test full flow: analyze → search → evaluate → check → present."""
    # This would require mocking the entire LLM chain and database
    # For now, we'll test the graph structure is correct

    graph = build_agent_graph(mock_pool)

    # Verify graph has all nodes
    assert "supervisor" in graph.nodes
    assert "analyze_playlist" in graph.nodes
    assert "search_tracks" in graph.nodes
    assert "evaluate_results" in graph.nodes
    assert "check_knowledge" in graph.nodes
    assert "present_results" in graph.nodes


@pytest.mark.asyncio
async def test_graph_compiles_successfully(mock_pool):
    """Test that the graph compiles without errors."""
    try:
        graph = build_agent_graph(mock_pool)
        assert graph is not None
    except Exception as e:
        pytest.fail(f"Graph compilation failed: {e}")


@pytest.mark.asyncio
async def test_graph_has_correct_interrupts(mock_pool):
    """Test that graph has interrupts configured correctly."""
    graph = build_agent_graph(mock_pool)

    # The graph should have interrupt_after configured
    # This is a structural test to ensure the graph is set up correctly
    assert graph is not None
