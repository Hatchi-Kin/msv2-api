"""Manual test script for Music Curator Agent v3.

Run this script to test the agent with a real playlist.

Usage:
    python tests/manual_agent_test_v3.py
"""

import asyncio
import asyncpg
from api.agents.gem_hunter.graph_v3 import build_agent_graph_v3
from api.agents.gem_hunter.state_v3 import AgentState
from api.core.config import settings
from api.core.logger import logger


async def test_agent_v3():
    """Test the v3 agent with a real playlist."""
    
    # Connect to database
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    
    try:
        # Build graph
        graph = build_agent_graph_v3(pool)
        
        # Test playlist ID (replace with your actual playlist ID)
        playlist_id = input("Enter playlist ID to test: ")
        
        # Initial state
        initial_state: AgentState = {
            "playlist_id": playlist_id,
            "user_id": "test_user",
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
        
        # Config
        thread_id = f"test_playlist_{playlist_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        print("\n" + "="*60)
        print("🎵 MUSIC CURATOR AGENT V3 - MANUAL TEST")
        print("="*60 + "\n")
        
        # Start agent
        print("▶️  Starting agent...")
        state = await graph.ainvoke(initial_state, config=config)
        
        # Print UI state
        ui_state = state.get("ui_state")
        if ui_state:
            print("\n📤 UI STATE:")
            print(f"Message: {ui_state.get('message')}")
            print(f"Options: {len(ui_state.get('options', []))} options")
            print(f"Cards: {len(ui_state.get('cards', []))} cards")
            
            if ui_state.get('options'):
                print("\nOptions:")
                for opt in ui_state['options']:
                    print(f"  - {opt['label']} ({opt['value']})")
        
        # Check if interrupted (waiting for vibe selection)
        if state.get("playlist_analyzed") and not state.get("vibe_choice"):
            print("\n⏸️  Agent interrupted - waiting for vibe selection")
            vibe = input("\nSelect vibe (similar/chill/energy/surprise): ")
            
            # Update state with vibe
            await graph.aupdate_state(config, {"vibe_choice": vibe})
            
            # Resume
            print("\n▶️  Resuming agent...")
            state = await graph.ainvoke(None, config=config)
            
            # Print UI state
            ui_state = state.get("ui_state")
            if ui_state:
                print("\n📤 UI STATE:")
                print(f"Message: {ui_state.get('message')}")
                print(f"Options: {len(ui_state.get('options', []))} options")
                print(f"Cards: {len(ui_state.get('cards', []))} cards")
                
                if ui_state.get('options'):
                    print("\nOptions:")
                    for opt in ui_state['options']:
                        print(f"  - {opt['label']} ({opt['value']})")
        
        # Check if interrupted (waiting for artist knowledge)
        if state.get("knowledge_checked") and not state.get("results_presented"):
            print("\n⏸️  Agent interrupted - waiting for artist knowledge")
            
            # Show artists
            candidates = state.get("candidate_tracks", [])
            artists = list(set(
                t.get("artist") if isinstance(t, dict) else t.artist
                for t in candidates[:20]
            ))
            
            print("\nArtists found:")
            for i, artist in enumerate(artists, 1):
                print(f"  {i}. {artist}")
            
            known = input("\nEnter known artist numbers (comma-separated) or 'none' or 'all': ")
            
            if known.lower() == "none":
                known_artists = []
            elif known.lower() == "all":
                known_artists = artists
            else:
                indices = [int(x.strip()) - 1 for x in known.split(",") if x.strip()]
                known_artists = [artists[i] for i in indices if i < len(artists)]
            
            # Update state with known artists
            await graph.aupdate_state(config, {"known_artists": known_artists})
            
            # Resume
            print("\n▶️  Resuming agent...")
            state = await graph.ainvoke(None, config=config)
            
            # Print UI state
            ui_state = state.get("ui_state")
            if ui_state:
                print("\n📤 FINAL UI STATE:")
                print(f"Message: {ui_state.get('message')}")
                print(f"Cards: {len(ui_state.get('cards', []))} cards")
                
                if ui_state.get('cards'):
                    print("\n" + "="*60)
                    print("🎁 YOUR CURATED PLAYLIST")
                    print("="*60)
                    for i, card in enumerate(ui_state['cards'], 1):
                        print(f"\n{i}. {card['title']}")
                        print(f"   Artist: {card['artist']}")
                        print(f"   Why: {card['reason']}")
                    print("\n" + "="*60)
        
        # Print final state
        print("\n" + "="*60)
        print("✅ AGENT COMPLETED")
        print("="*60)
        print(f"Iterations: {state.get('iteration_count')}")
        print(f"Search iterations: {state.get('search_iteration')}")
        print(f"Known artists: {len(state.get('known_artists', []))}")
        print(f"Final tracks: {len(state.get('ui_state', {}).get('cards', []))}")
        
        # Print supervisor reasoning
        print("\n🧠 Supervisor Reasoning:")
        print(f"  {state.get('supervisor_reasoning')}")
        
        # Print action history
        print("\n📜 Action History:")
        for action in state.get('action_history', []):
            print(f"  - {action}")
        
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(test_agent_v3())
