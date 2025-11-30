import asyncio
import os
import uuid
import asyncpg
from api.core.config import settings
from api.core.config import settings
from api.core.db_codecs import register_vector_codec
from api.agents.gem_hunter.graph import build_agent_graph
from langgraph.checkpoint.memory import MemorySaver

async def main():
    print("Starting Gem Hunter Agent V2 CLI...")
    
    # Setup DB Pool with vector codec
    async def init_db(conn):
        await register_vector_codec(conn)
        
    pool = await asyncpg.create_pool(settings.DATABASE_URL, init=init_db)
    
    # Use MemorySaver for now to test logic
    checkpointer = MemorySaver()
    # await checkpointer.setup() # MemorySaver doesn't need setup
    
    # Build Graph
    app = build_agent_graph(pool, checkpointer)
    
    # Input
    playlist_id = input("Enter Playlist ID (default: 1): ") or "1"
    user_id = "test_user"
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initial State
    initial_state = {
        "playlist_id": playlist_id,
        "user_id": user_id,
        "playlist_analyzed": False,
        "vibe_selected": False,
        "search_done": False,
        "enriched": False,
        "filtered": False,
        "knowledge_checked": False,
        "knowledge_search_attempted": False,
        "known_artists": [],
        "excluded_artists": []
    }
    
    print(f"\n🚀 Starting Thread: {thread_id}")
    
    # 1. Start (Runs until analyze_playlist interrupt)
    print("\n--- Phase 1: Analyzing Playlist ---")
    async for event in app.astream(initial_state, config=config):
        for key, value in event.items():
            print(f"Node: {key}")
            if value and "ui_state" in value:
                print(f"🤖 Message: {value['ui_state']['message']}")
                
    # Check state
    state = await app.aget_state(config)
    print(f"⏸️ Paused. Next: {state.next}")
    
    # 2. User Input (Vibe)
    # We assume we are paused after analyze_playlist
    if state.values.get("playlist_analyzed") and not state.values.get("vibe_selected"):
        # Show options
        ui_state = state.values["ui_state"]
        print("\nOptions:")
        for i, opt in enumerate(ui_state["options"]):
            print(f"{i+1}. {opt['label']}")
            
        choice_idx = int(input("\nSelect option: ")) - 1
        choice = ui_state["options"][choice_idx]["value"]
        
        # Update State
        print(f"👉 Selected: {choice}")
        await app.aupdate_state(config, {
            "vibe_choice": choice,
            "vibe_selected": True
        })
        
        # Resume
        print("\n--- Phase 2: Searching & Filtering ---")
        async for event in app.astream(None, config=config):
            for key, value in event.items():
                print(f"Node: {key}")
                if value and "ui_state" in value:
                    print(f"🤖 Message: {value['ui_state']['message']}")

    # 3. User Input (Knowledge) - Loop to handle re-search
    max_iterations = 3
    iteration = 0
    
    while iteration < max_iterations:
        state = await app.aget_state(config)
        
        # Check if we're done (no more interrupts)
        if not state.next:
            print("\n✅ Agent completed!")
            break
            
        if state.values.get("knowledge_checked"):
            iteration += 1
            print(f"\n--- Knowledge Check (Iteration {iteration}) ---")
            
            ui_state = state.values["ui_state"]
            print("\nOptions:")
            for i, opt in enumerate(ui_state["options"]):
                print(f"{i+1}. {opt['label']}")
                
            print("(Enter comma-separated indices, e.g. 1,3 or 'all' or 'none')")
            selection = input("\nSelect known artists: ")
            
            known = []
            if selection.lower() == "all":
                # User typed "all" directly
                known = [opt["value"] for opt in ui_state["options"] if opt["value"] not in ["all", "none"]]
            elif selection.lower() == "none":
                # User typed "none" directly
                known = []
            else:
                try:
                    indices = [int(x.strip())-1 for x in selection.split(",")]
                    selected_values = [ui_state["options"][i]["value"] for i in indices]
                    
                    # Check if user selected the "all" or "none" options
                    if "all" in selected_values:
                        # Expand "all" to all actual artists
                        known = [opt["value"] for opt in ui_state["options"] if opt["value"] not in ["all", "none"]]
                    elif "none" in selected_values:
                        known = []
                    else:
                        # Regular artist selection
                        known = selected_values
                except:
                    print("Invalid input, assuming none.")
                    known = []
                
            # Update State
            print(f"👉 Known Artists: {known}")
            
            # We need to append to existing known artists
            existing = state.values.get("known_artists", [])
            all_known = list(set(existing + known))
            
            await app.aupdate_state(config, {
                "known_artists": all_known
            })
            
            # Resume
            print(f"\n--- Processing (Iteration {iteration}) ---")
            async for event in app.astream(None, config=config):
                for key, value in event.items():
                    print(f"Node: {key}")
                    if value and "ui_state" in value:
                        print(f"🤖 Message: {value['ui_state']['message']}")
                        if "cards" in value["ui_state"]:
                            print(f"\n🎵 Found {len(value['ui_state']['cards'])} tracks:")
                            for card in value["ui_state"]["cards"]:
                                print(f"  • {card['title']} - {card['artist']}")
                                print(f"    {card['reason']}")
        else:
            print("\n⚠️ Unexpected state - exiting")
            break

if __name__ == "__main__":
    asyncio.run(main())
