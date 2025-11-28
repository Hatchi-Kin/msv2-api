"""LLM-powered pitch generation - creates compelling track descriptions."""

from typing import List, Dict

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from api.core.logger import logger
from api.agents.gem_hunter.exceptions import LLMFailureError


class Pitch(BaseModel):
    """A pitch for a single track."""

    track_id: int
    hook: str = Field(description="A 1-sentence persuasive hook for the user.")


class PitchList(BaseModel):
    """List of pitches."""

    pitches: List[Pitch]


async def generate_pitches(
    tracks: List[dict], vibe_choice: str, user_preferences: str, llm
) -> Dict[int, str]:
    """Generate descriptive characteristics for each track.

    Args:
        tracks: List of track dictionaries with metadata
        vibe_choice: User's selected vibe
        user_preferences: User's general preferences
        llm: LangChain LLM instance

    Returns:
        Dictionary mapping track_id to pitch text
    """
    # Build context for each track with ID mapping
    track_contexts = []
    for t in tracks:
        # Get musical characteristics
        genre = t.get("genre") or (
            t.get("top_5_genres", "").split(",")[0].strip()
            if t.get("top_5_genres")
            else None
        )
        bpm = t.get("bpm")
        energy = t.get("energy") or 0
        acousticness = t.get("acousticness") or 0
        danceability = t.get("danceability") or 0

        # Build feature description
        features = []
        if bpm:
            if bpm > 140:
                features.append("fast-paced")
            elif bpm > 120:
                features.append("upbeat")
            elif bpm < 90:
                features.append("slow")
            else:
                features.append("mid-tempo")

        if energy > 0.7:
            features.append("energetic")
        elif energy < 0.4:
            features.append("mellow")

        if acousticness > 0.6:
            features.append("acoustic")
        elif acousticness < 0.2:
            features.append("electronic")

        if danceability > 0.7:
            features.append("danceable")

        context = f"""
        ID: {t['id']}
        Title: {t.get('title')}
        Artist: {t.get('artist')}
        Genre: {genre or 'Unknown'}
        Characteristics: {', '.join(features) if features else 'balanced'}
        """
        track_contexts.append(context)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a music curator. For each track, write a SHORT descriptive phrase (5-8 words max) that captures its musical essence.

RULES:
1. Be CONCISE - no more than 8 words
2. Focus on MUSICAL characteristics: tempo feel, instrumentation, vocals, mood
3. Use descriptive language: "driving synths", "deep female vocals", "dreamy atmosphere"
4. NO generic phrases like "recommended for you" or "great track"
5. You MUST include the track ID in your response

Examples:
- "High-tempo electronic with driving synths"
- "Mellow acoustic featuring deep female vocals"
- "Upbeat indie rock with catchy guitar riffs"
- "Atmospheric downtempo with ethereal soundscapes"
""",
            ),
            ("human", "Tracks:\n{tracks}"),
        ]
    )

    structured_llm = llm.with_structured_output(PitchList)
    chain = prompt | structured_llm

    try:
        result = await chain.ainvoke({"tracks": "\n".join(track_contexts)})
        pitches_dict = {p.track_id: p.hook for p in result.pitches}
        logger.info(
            f"✅ Generated {len(pitches_dict)} pitches for {len(tracks)} tracks"
        )
        logger.debug(f"Pitches: {pitches_dict}")
        return pitches_dict
    except Exception as e:
        logger.error(f"❌ Pitch generation failed: {e}", exc_info=True)
        raise LLMFailureError(f"Failed to generate track descriptions: {e}")
