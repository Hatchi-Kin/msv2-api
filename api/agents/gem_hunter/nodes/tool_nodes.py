import asyncpg
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from api.agents.gem_hunter.state import AgentState, UIState
from api.agents.gem_hunter.tools import search_tool
from api.agents.gem_hunter.llm_factory import get_llm
from api.core.logger import logger
from api.core.config import settings

class ToolNodes:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        # Initialize LLMs
        self.creative_llm = get_llm(model=settings.LLM_CREATIVE_MODEL, temperature=0.7)
        self.reasoning_llm = get_llm(model=settings.LLM_REASONING_MODEL, temperature=0.0)

    async def analyze_playlist(self, state: AgentState) -> Dict[str, Any]:
        """Step 2: Analyze playlist and ask for vibe."""
        logger.info("--- Node: Analyze Playlist ---")
        playlist_id = state["playlist_id"]
        
        # 1. Get stats
        stats = await search_tool.analyze_playlist_stats(self.pool, int(playlist_id))
        logger.info(f"📊 Playlist stats: {stats}")
        
        # 2. Generate description
        prompt = ChatPromptTemplate.from_template(
            "Describe this playlist vibe in 1 sentence based on stats: {stats}"
        )
        chain = prompt | self.creative_llm
        desc = await chain.ainvoke({"stats": stats})
        
        # 3. Create UI Options
        options = [
            {"label": "🔥 More of this (Similar Vibe)", "value": "similar"},
            {"label": "😌 Dial it down (Chill)", "value": "chill"},
            {"label": "⚡ Pump it up (High Energy)", "value": "energy"},
            {"label": "🌟 Surprise me", "value": "surprise"}
        ]
        
        message = f"I analyzed your playlist.\n\n📊 **Stats:**\n• BPM: {stats.get('avg_bpm') or 0:.0f}\n• Genres: {', '.join(stats.get('top_genres', []))}\n\n💭 **Vibe:** {desc.content}\n\nWhat direction should I explore?"
        
        return {
            "playlist_profile": stats,
            "playlist_analyzed": True,
            "ui_state": {"message": message, "options": options, "cards": [], "thought_process": []}
        }

    async def search_tracks(self, state: AgentState) -> Dict[str, Any]:
        """Step 3: Search for candidates."""
        logger.info("--- Node: Search Tracks ---")
        
        # Determine constraints based on vibe_choice
        vibe = state.get("vibe_choice", "similar")
        constraints = {}
        
        if vibe == "chill":
            constraints = {"max_energy": 0.6, "max_bpm": 110}
        elif vibe == "energy":
            constraints = {"min_energy": 0.7, "min_bpm": 120}
            
        # Search
        candidates = await search_tool.search_similar_tracks(
            self.pool,
            int(state["playlist_id"]),
            constraints,
            exclude_ids=[],
            exclude_artists=state.get("excluded_artists", []),
            limit=50
        )
        
        return {
            "candidate_tracks": candidates,
            "constraints": constraints,
            "search_done": True,
            "enriched": False, # Reset downstream flags
            "filtered": False,
            "knowledge_checked": False
        }

    async def enrich_tracks(self, state: AgentState) -> Dict[str, Any]:
        """Step 4: Enrich tracks (currently pass-through)."""
        logger.info("--- Node: Enrich Tracks ---")
        return {
            "enriched_tracks": state["candidate_tracks"],
            "enriched": True
        }

    async def filter_tracks(self, state: AgentState) -> Dict[str, Any]:
        """Step 5: Filter tracks."""
        logger.info("--- Node: Filter Tracks ---")
        tracks = state["enriched_tracks"]
        constraints = state.get("constraints", {})
        
        # Apply strict filtering
        filtered = search_tool.filter_tracks_strict(tracks, constraints)
        
        # Limit to top 10
        final = filtered[:10]
        
        return {
            "final_tracks": final,
            "filtered": True
        }

    async def check_knowledge(self, state: AgentState) -> Dict[str, Any]:
        """Step 6: Check artist knowledge."""
        logger.info("--- Node: Check Knowledge ---")
        tracks = state["final_tracks"]
        
        # Extract unique artists
        artists = list(set(
            (t["artist"] if isinstance(t, dict) else t.artist) 
            for t in tracks
        ))
        
        options = [{"label": artist, "value": artist} for artist in artists]
        options.append({"label": "None of them", "value": "none"})
        options.append({"label": "All of them", "value": "all"})
        
        message = "Do you know any of these artists? Select the ones you know:"
        
        return {
            "knowledge_checked": True,
            "ui_state": {
                "message": message,
                "options": options,
                "cards": [], # Don't show cards yet
                "thought_process": []
            }
        }

    async def process_knowledge(self, state: AgentState) -> Dict[str, Any]:
        """Step 7: Process knowledge and decide next step."""
        logger.info("--- Node: Process Knowledge ---")
        
        final_tracks = state.get("final_tracks", [])
        known = state.get("known_artists", [])
        
        # Filter final_tracks against known
        unknown_tracks = []
        for t in final_tracks:
            artist = t["artist"] if isinstance(t, dict) else t.artist
            if artist not in known:
                unknown_tracks.append(t)
        
        if len(unknown_tracks) == 0:
            # User knows ALL.
            if not state.get("knowledge_search_attempted", False):
                logger.info("🔄 User knows all! Re-searching with excluded artists...")
                return {
                    "knowledge_search_attempted": True,
                    "excluded_artists": state.get("excluded_artists", []) + known,
                    "search_done": False, # Trigger re-search
                    "enriched": False,
                    "filtered": False,
                    "knowledge_checked": True  # KEEP THIS TRUE - skip second check
                }
            else:
                logger.info("✅ Second search done, proceeding to present")
                return {} # Proceed to present (will show the new tracks)
        
        return {} # Proceed to present

    async def present_results(self, state: AgentState) -> Dict[str, Any]:
        """Step 8: Present results."""
        logger.info("--- Node: Present Results ---")
        tracks = state["final_tracks"]
        known = state.get("known_artists", [])
        
        # Filter out known artists UNLESS we've exhausted options
        # (knowledge_search_attempted means we already tried re-searching)
        if state.get("knowledge_search_attempted", False):
            # We've tried re-searching, show whatever we have
            logger.info("⚠️ Showing all tracks (exhausted re-search)")
            unknown_tracks = tracks
        else:
            # Normal filtering
            unknown_tracks = []
            for t in tracks:
                artist = t["artist"] if isinstance(t, dict) else t.artist
                if artist not in known:
                    unknown_tracks.append(t)
        
        # Take top 5
        selection = unknown_tracks[:5]
        
        # Generate Pitches
        cards = []
        for t in selection:
            # Access attributes safely
            t_id = t["id"] if isinstance(t, dict) else t.id
            t_title = t["title"] if isinstance(t, dict) else t.title
            t_artist = t["artist"] if isinstance(t, dict) else t.artist
            
            prompt = ChatPromptTemplate.from_template(
                "Write a 1-sentence pitch for this track: {track}. Why is it a hidden gem?"
            )
            chain = prompt | self.creative_llm
            pitch = await chain.ainvoke({"track": str(t)})
            
            cards.append({
                "id": t_id,
                "title": t_title,
                "artist": t_artist,
                "reason": pitch.content
            })
            
        return {
            "results_presented": True,
            "ui_state": {
                "message": "Here are some hidden gems I found for you!",
                "cards": cards,
                "options": [{"label": "Save Playlist", "value": "save"}],
                "thought_process": []
            }
        }
