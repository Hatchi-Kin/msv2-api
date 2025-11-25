"""LangGraph definition for the Hidden Gem Hunter agent."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import asyncpg

from api.agents.gem_hunter.state import AgentState
from api.agents.gem_hunter.nodes.discovery_node import DiscoveryNode
from api.agents.gem_hunter.nodes.analysis_node import AnalysisNode
from api.agents.gem_hunter.nodes.presentation_node import PresentationNode


def build_agent_graph(pool: asyncpg.Pool, checkpointer=None):
    """
    Builds and compiles the Hidden Gem Hunter LangGraph agent.
    
    Args:
        pool: AsyncPG connection pool
        checkpointer: LangGraph checkpointer for state persistence
        
    Returns:
        Compiled LangGraph application
    """
    # 1. Initialize Nodes with DB Pool
    discovery = DiscoveryNode(pool)
    analysis = AnalysisNode(pool)
    presentation = PresentationNode(pool)

    # 2. Define Graph
    workflow = StateGraph(AgentState)

    # 3. Add Nodes
    workflow.add_node("discovery", discovery.execute)
    workflow.add_node("analysis", analysis.execute)
    workflow.add_node("presentation", presentation.execute)

    # 4. Add Edges
    workflow.add_edge(START, "discovery")

    # Conditional edge from discovery
    def check_discovery(state: AgentState):
        if state.get("next_step") == "end":
            return END
        return "analysis"

    workflow.add_conditional_edges("discovery", check_discovery)

    # Conditional edge from analysis (loop or proceed)
    def check_analysis(state: AgentState):
        if state.get("next_step") == "end":
            return END
        if state.get("next_step") == "discovery":
            return "discovery"  # Loop back to get more candidates
        if state.get("next_step") == "presentation":
            return "presentation"
        return "analysis"  # Loop back to self

    workflow.add_conditional_edges("analysis", check_analysis)

    # Conditional edge from presentation (pause for vibe or finish)
    def check_presentation(state: AgentState):
        if state.get("next_step") == "end":
            return END
        return "presentation"  # Loop back to generate pitches after vibe selection

    workflow.add_conditional_edges("presentation", check_presentation)

    # 5. Compile with Checkpointer
    if checkpointer is None:
        checkpointer = MemorySaver()

    app = workflow.compile(checkpointer=checkpointer)

    return app
