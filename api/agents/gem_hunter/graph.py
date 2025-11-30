from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from api.agents.gem_hunter.state import AgentState
from api.agents.gem_hunter.nodes.tool_nodes import ToolNodes
import asyncpg

def build_agent_graph(pool: asyncpg.Pool, checkpointer=None):
    # 1. Initialize Nodes
    nodes = ToolNodes(pool)
    
    # 2. Build Graph
    workflow = StateGraph(AgentState)
    
    # 3. Add Nodes
    workflow.add_node("analyze_playlist", nodes.analyze_playlist)
    workflow.add_node("search_tracks", nodes.search_tracks)
    workflow.add_node("enrich_tracks", nodes.enrich_tracks)
    workflow.add_node("filter_tracks", nodes.filter_tracks)
    workflow.add_node("check_knowledge", nodes.check_knowledge)
    workflow.add_node("process_knowledge", nodes.process_knowledge)
    workflow.add_node("present_results", nodes.present_results)
    
    # 4. Define Edges (The State Machine)
    
    # Start -> Analyze
    workflow.add_edge(START, "analyze_playlist")
    
    # Analyze -> Wait for User (Interrupt) -> Search
    workflow.add_edge("analyze_playlist", "search_tracks")
    
    # Search -> Enrich -> Filter -> Check Knowledge (conditionally)
    workflow.add_edge("search_tracks", "enrich_tracks")
    workflow.add_edge("enrich_tracks", "filter_tracks")
    
    # After filter, check if we should ask about knowledge or skip to process
    def route_after_filter(state: AgentState):
        # If knowledge already checked (re-search scenario), skip to process
        if state.get("knowledge_checked") and state.get("knowledge_search_attempted"):
            return "process_knowledge"
        return "check_knowledge"
        
    workflow.add_conditional_edges("filter_tracks", route_after_filter, {
        "check_knowledge": "check_knowledge",
        "process_knowledge": "process_knowledge"
    })
    
    # Check Knowledge -> Wait for User (Interrupt) -> Process
    workflow.add_edge("check_knowledge", "process_knowledge")
    
    # Process -> Loop or Present
    def route_after_process(state: AgentState):
        # If we reset search_done (due to "All Known"), loop back
        if not state.get("search_done"):
            return "search_tracks"
        return "present_results"
        
    workflow.add_conditional_edges("process_knowledge", route_after_process)
    
    # Present -> End
    workflow.add_edge("present_results", END)
    
    # 5. Compile
    if checkpointer is None:
        checkpointer = MemorySaver()
        
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_after=["analyze_playlist", "check_knowledge"]
    )
    
    return app
