"""LLM-powered playlist analysis - generates natural language understanding."""

from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate

from api.core.logger import logger


async def generate_playlist_analysis(profile: Dict[str, Any], llm) -> str:
    """Generate natural language analysis of the playlist using LLM.

    Args:
        profile: Playlist profile dictionary from build_playlist_profile()
        llm: LangChain LLM instance

    Returns:
        Natural language analysis string
    """
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a music curator analyzing a user's playlist. 

Write a 2-3 sentence analysis that:
1. Describes the overall musical style/vibe
2. Mentions key characteristics (genres, energy, tempo if available)
3. Sounds natural and conversational (not robotic)

Keep it concise and insightful.""",
                ),
                (
                    "human",
                    """Analyze this playlist:

Track count: {track_count}
Top genres: {genres}
Key artists: {artists}
Average BPM: {avg_bpm}
Average energy: {avg_energy}%
Sample tracks: {sample_tracks}

Write a natural, conversational analysis:""",
                ),
            ]
        )

        chain = prompt | llm

        result = await chain.ainvoke(
            {
                "track_count": profile["track_count"],
                "genres": (
                    ", ".join(profile["genres"]) if profile["genres"] else "Various"
                ),
                "artists": (
                    ", ".join(profile["artists"])
                    if profile["artists"]
                    else "Various artists"
                ),
                "avg_bpm": profile["avg_bpm"] or "N/A",
                "avg_energy": profile["avg_energy"] or "N/A",
                "sample_tracks": (
                    "\n".join(profile["sample_tracks"])
                    if profile["sample_tracks"]
                    else "N/A"
                ),
            }
        )

        # Extract text from AIMessage
        analysis = result.content if hasattr(result, "content") else str(result)

        logger.info(f"Generated playlist analysis: {analysis[:30]}...")
        return analysis.strip()

    except Exception as e:
        logger.error(f"Failed to generate playlist analysis: {e}")
        # Fallback to simple template
        genres_str = (
            ", ".join(profile["genres"][:3]) if profile["genres"] else "various genres"
        )
        return f"I've analyzed your playlist of {profile['track_count']} tracks. Your collection features {genres_str} with a diverse mix of artists."
