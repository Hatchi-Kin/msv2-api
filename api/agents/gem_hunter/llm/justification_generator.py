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

        # Add metrics if available
        metrics = []
        if t.get("energy"):
            metrics.append(f"Energy: {t['energy']:.2f}")
        if t.get("valence"):
            metrics.append(f"Valence: {t['valence']:.2f}")

        if metrics:
            parts.append(f"({', '.join(metrics)})")

        track_summaries.append(" - ".join(parts))

    # Generate structured justification with LLM
    # Note: When using json_mode, the prompt MUST explicitly ask for JSON
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a music expert helping users discover hidden gems. 
Analyze the user's playlist profile and the selected tracks to provide a personalized explanation.

You MUST respond with a valid JSON object with exactly these two fields:
{{
  "understanding": "Explain what you understood about the user's playlist (genres, tempo, energy).",
  "selection": "Explain how your selected tracks match that vibe and the user's preference."
}}

Be specific, enthusiastic, and natural. Keep each field to 2-3 sentences maximum.
IMPORTANT: Reference the audio metrics (Energy, Valence) provided in the track list to justify your choice (e.g., "I chose this because its high energy (0.85) matches your workout vibe").
Don't list track names in the text.

Respond ONLY with valid JSON, no other text.
""",
            ),
            (
                "human",
                """Playlist Profile: {profile}
User's Vibe Choice: {vibe}
Selected Tracks: {tracks}

JSON response:""",
            ),
        ]
    )

    # Use structured output
    # Note: Using method="json_mode" for better Gemini 2.5 compatibility
    # The default method can return None with Gemini 2.5 models due to malformed function calls
    structured_llm = llm.with_structured_output(Justification, method="json_mode")
    chain = prompt | structured_llm

    try:
        response: Justification = await chain.ainvoke(
            {
                "profile": str(playlist_profile),
                "vibe": vibe_choice,
                "tracks": "\n".join(track_summaries),
            }
        )

        # Sanity check (should not be None with json_mode, but just in case)
        if response is None:
            logger.error("⚠️ LLM returned None even with json_mode")
            raise LLMFailureError("LLM returned None response")

        return response
    except Exception as e:
        logger.error(f"❌ Justification generation failed: {e}", exc_info=True)
        raise LLMFailureError(f"Failed to generate recommendation explanation: {e}")
