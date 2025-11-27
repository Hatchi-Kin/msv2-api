"""LLM-powered justification generation - explains recommendation rationale."""

from typing import List
from collections import Counter
from langchain_core.prompts import ChatPromptTemplate
from api.core.logger import logger
from api.agents.gem_hunter.exceptions import LLMFailureError
from api.agents.gem_hunter.models import Justification


async def generate_justification(
    tracks: List[dict],
    vibe_choice: str,
    playlist_id: int,
    candidate_tracks: List[dict],
    llm,
) -> Justification:
    """Generate a two-part message: playlist understanding + selection rationale.
    
    Args:
        tracks: Final selected tracks
        vibe_choice: User's vibe selection
        playlist_id: ID of the playlist
        candidate_tracks: Original candidate tracks before filtering
        llm: LangChain LLM instance
        
    Returns:
        Natural language justification string
    """
    # Analyze the candidate tracks to understand the playlist
    # Get playlist characteristics from candidates
    genres = []
    tempos = []
    energies = []

    for t in candidate_tracks[:10]:  # Sample first 10 for analysis
        if t.get("genre"):
            genres.append(t["genre"])
        elif t.get("top_5_genres"):
            top_genre = t["top_5_genres"].split(",")[0].strip()
            if top_genre:
                genres.append(top_genre)

        if t.get("bpm"):
            tempos.append(t["bpm"])
        if t.get("energy"):
            energies.append(t["energy"])

    # Build playlist profile
    playlist_profile = {}
    if genres:
        genre_counts = Counter(genres)
        top_genres = [g for g, _ in genre_counts.most_common(3)]
        playlist_profile["genres"] = top_genres

    if tempos:
        avg_tempo = sum(tempos) / len(tempos)
        if avg_tempo > 130:
            playlist_profile["tempo"] = "high-energy, fast-paced"
        elif avg_tempo > 110:
            playlist_profile["tempo"] = "upbeat, moderate"
        elif avg_tempo < 95:
            playlist_profile["tempo"] = "slow, relaxed"
        else:
            playlist_profile["tempo"] = "balanced"

    if energies:
        avg_energy = sum(energies) / len(energies)
        if avg_energy > 0.7:
            playlist_profile["energy"] = "intense and driving"
        elif avg_energy > 0.5:
            playlist_profile["energy"] = "moderately energetic"
        else:
            playlist_profile["energy"] = "mellow and laid-back"

    # Build track summaries for selection description
    track_summaries = []
    for t in tracks:
        parts = [f"{t['title']} by {t['artist']}"]
        if t.get("genre"):
            parts.append(t["genre"])
        track_summaries.append(" - ".join(parts))

    # Generate structured justification with LLM
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a music expert helping users discover hidden gems. 
Analyze the user's playlist profile and the selected tracks to provide a personalized explanation.

Your output must be a structured object with two fields:
1. `understanding`: Explain what you understood about the user's playlist (genres, tempo, energy).
2. `selection`: Explain how your selected tracks match that vibe and the user's preference.

Be specific, enthusiastic, and natural. Don't list track names in the text.
""",
            ),
            (
                "human",
                """Playlist Profile: {profile}
User's Vibe Choice: {vibe}
Selected Tracks: {tracks}""",
            ),
        ]
    )

    # Use structured output
    structured_llm = llm.with_structured_output(Justification)
    chain = prompt | structured_llm

    try:
        response: Justification = await chain.ainvoke(
            {
                "profile": str(playlist_profile),
                "vibe": vibe_choice,
                "tracks": "\n".join(track_summaries),
            }
        )
        return response
    except Exception as e:
        logger.error(f"❌ Justification generation failed: {e}", exc_info=True)
        raise LLMFailureError(f"Failed to generate recommendation explanation: {e}")
