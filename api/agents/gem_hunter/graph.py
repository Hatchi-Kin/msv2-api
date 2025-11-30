"""LangGraph definition for Music Curator Agent v3 (Supervisor Pattern)."""

import asyncpg
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from api.agents.gem_hunter.state import AgentState
from api.agents.gem_hunter.nodes.supervisor import SupervisorNode
from api.agents.gem_hunter.nodes.tools import ToolNodes


def build_agent_graph(pool: asyncpg.Pool, checkpointer=None):
    """Build the supervisor-based music curator agent."""

    # Initialize nodes
    supervisor = SupervisorNode()
    tools = ToolNodes(pool)

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("supervisor", supervisor.execute)
    workflow.add_node("analyze_playlist", tools.analyze_playlist)
    workflow.add_node("search_tracks", tools.search_tracks)
    workflow.add_node("evaluate_results", tools.evaluate_results)
    workflow.add_node("check_knowledge", tools.check_knowledge)
    workflow.add_node("present_results", tools.present_results)

    # Define edges
    workflow.add_edge(START, "supervisor")

    # Supervisor routes to tools or END
    def route_supervisor(state: AgentState):
        # Handle both dict and Pydantic model
        if isinstance(state, dict):
            action = state.get("next_action")
        else:
            action = state.next_action
        if action == "END":
            return END
        return action

    workflow.add_conditional_edges("supervisor", route_supervisor)

    # All tools return to supervisor (except present_results)
    workflow.add_edge("analyze_playlist", "supervisor")
    workflow.add_edge("search_tracks", "supervisor")
    workflow.add_edge("evaluate_results", "supervisor")
    workflow.add_edge("check_knowledge", "supervisor")
    workflow.add_edge("present_results", END)

    # Compile with checkpointer and interrupts
    if checkpointer is None:
        checkpointer = MemorySaver()

    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_after=["analyze_playlist", "check_knowledge"],
    )

    return app
