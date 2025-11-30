"""Tool nodes for Music Curator Agent v3."""

from typing import Dict, Any

import asyncpg
from langchain_core.prompts import ChatPromptTemplate

from api.agents.gem_hunter.state import AgentState
from api.agents.gem_hunter.llm_factory import get_llm
from api.core.config import settings
from api.core.logger import logger


class ToolNodes:
    """All tool implementations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.creative_llm = get_llm(model=settings.LLM_CREATIVE_MODEL, temperature=0.7)
        self.reasoning_llm = get_llm(
            model=settings.LLM_REASONING_MODEL, temperature=0.0
        )

    async def analyze_playlist(self, state: AgentState) -> Dict[str, Any]:
        """Analyze playlist and ask for vibe."""
        logger.info("🎵 Tool: Analyze Playlist")

        # Handle both dict and Pydantic model
        if isinstance(state, dict):
            state = AgentState(**state)

        try:
            from api.agents.gem_hunter.tools import search_tool

            playlist_id = int(state.playlist_id)
            stats = await search_tool.analyze_playlist_stats(self.pool, playlist_id)

            # Check if playlist is empty or too small
            track_count = stats.get("track_count", 0)
            if track_count < 5:
                return {
                    "error": f"Playlist has only {track_count} tracks. Please add at least 5 tracks to get recommendations.",
                    "ui_state": {
                        "message": f"Your playlist needs more tracks! It currently has {track_count} tracks, but I need at least 5 to understand your taste. Add some more songs and try again.",
                        "options": [],
                        "cards": [],
                        "thought_process": [
                            f"Playlist too small: {track_count} tracks"
                        ],
                    },
                }

            # Generate description (rule-based for speed)
            bpm = stats.get("avg_bpm", 120)
            energy = stats.get("avg_energy", 0.5)
            genres = stats.get("top_genres", [])

            # Tempo description
            if bpm < 90:
                tempo_desc = "slow, contemplative"
            elif bpm < 120:
                tempo_desc = "moderate, relaxed"
            elif bpm < 140:
                tempo_desc = "upbeat, energetic"
            else:
                tempo_desc = "fast-paced, driving"

            # Energy description
            if energy < 0.3:
                energy_desc = "mellow and intimate"
            elif energy < 0.6:
                energy_desc = "balanced and dynamic"
            else:
                energy_desc = "intense and powerful"

            # Genre description
            genre_desc = f"{', '.join(genres[:2])}" if genres else "eclectic"

            desc = f"This playlist has a {tempo_desc} tempo with {energy_desc} vibes, featuring {genre_desc} influences."
            stats["description"] = desc

            # Create options
            options = [
                {"label": "🔥 More of this", "value": "similar"},
                {"label": "😌 Chill", "value": "chill"},
                {"label": "⚡ Energy", "value": "energy"},
                {"label": "🌟 Surprise", "value": "surprise"},
            ]

            message = f"I analyzed your playlist.\n\n📊 BPM: {stats.get('avg_bpm', 0):.0f}, Energy: {stats.get('avg_energy', 0):.2f}\n\n💭 {stats['description']}\n\nWhat vibe should I explore?"

            return {
                "playlist_analyzed": True,
                "playlist_profile": stats,
                "ui_state": {
                    "message": message,
                    "options": options,
                    "cards": [],
                    "thought_process": [
                        f"Analyzed playlist with {stats.get('track_count', 0)} tracks"
                    ],
                },
            }
        except Exception as e:
            logger.error(f"❌ analyze_playlist failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "ui_state": {
                    "message": "Sorry, I couldn't analyze your playlist. Please try again.",
                    "options": [],
                    "cards": [],
                    "thought_process": [f"Error during analysis: {str(e)}"],
                },
            }

    async def search_tracks(self, state: AgentState) -> Dict[str, Any]:
        """Search for similar tracks."""
        logger.info("🔍 Tool: Search Tracks")

        # Handle both dict and Pydantic model
        if isinstance(state, dict):
            state = AgentState(**state)

        try:
            from api.agents.gem_hunter.tools import search_tool

            playlist_id = int(state.playlist_id)
            vibe = state.vibe_choice or "similar"
            iteration = state.search_iteration + 1
            excluded = state.known_artists
            _params = state.tool_parameters

            # Build constraints based on vibe
            profile = state.playlist_profile or {}
            avg_bpm = profile.get("avg_bpm", 120)

            if vibe == "chill":
                constraints = {"max_energy": 0.6, "max_bpm": 110}
            elif vibe == "energy":
                constraints = {"min_energy": 0.7, "min_bpm": 120}
            elif vibe == "similar":
                constraints = {"min_bpm": max(0, avg_bpm - 20), "max_bpm": avg_bpm + 20}
            else:  # surprise
                constraints = {}

            # Adaptive: Relax constraints on retry
            if iteration > 1:
                logger.info(f"🔄 Search iteration {iteration}, relaxing constraints")
                if "min_bpm" in constraints:
                    constraints["min_bpm"] = max(0, constraints["min_bpm"] - 10)
                if "max_bpm" in constraints:
                    constraints["max_bpm"] = constraints["max_bpm"] + 10
                if "min_energy" in constraints:
                    constraints["min_energy"] = max(0, constraints["min_energy"] - 0.1)
                if "max_energy" in constraints:
                    constraints["max_energy"] = min(
                        1.0, constraints["max_energy"] + 0.1
                    )

            # Search
            limit = 50 if iteration == 1 else 100
            candidates = await search_tool.search_similar_tracks(
                self.pool,
                playlist_id,
                constraints,
                exclude_ids=[],
                exclude_artists=excluded,
                limit=limit,
            )

            logger.info(f"✅ Found {len(candidates)} candidates")

            # Check if database has insufficient tracks
            if len(candidates) == 0 and iteration == 1:
                logger.warning("⚠️ No candidates found on first search")

            # Convert Track objects to dicts for LangGraph state
            candidates_dicts = [t.model_dump() for t in candidates]

            return {"candidate_tracks": candidates_dicts, "search_iteration": iteration}
        except Exception as e:
            logger.error(f"❌ search_tracks failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "candidate_tracks": [],
                "search_iteration": state.search_iteration + 1,
            }

    async def evaluate_results(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate quality of candidates."""
        logger.info("📊 Tool: Evaluate Results")

        # Handle both dict and Pydantic model
        if isinstance(state, dict):
            state = AgentState(**state)

        candidates = state.candidate_tracks

        if len(candidates) == 0:
            return {
                "quality_assessment": {
                    "sufficient": False,
                    "quality_score": 0.0,
                    "recommendation": "search_again",
                }
            }

        # Quantity score
        quantity_score = min(len(candidates) / 50, 1.0)

        # Quality score (similarity)
        distances = [
            t.get("distance") if isinstance(t, dict) else t.distance for t in candidates
        ]
        # Filter out None values and use 0.5 as default
        valid_distances = [d for d in distances if d is not None]
        avg_distance = (
            sum(valid_distances) / len(valid_distances) if valid_distances else 0.5
        )
        quality_score = 1.0 - avg_distance

        # Diversity score
        artists = set(
            t.get("artist") if isinstance(t, dict) else t.artist for t in candidates
        )
        diversity_score = min(len(artists) / 20, 1.0)

        # Overall
        overall = (quantity_score + quality_score + diversity_score) / 3

        assessment = {
            "sufficient": overall > 0.6,
            "quality_score": overall,
            "recommendation": "proceed" if overall > 0.6 else "search_again",
        }

        logger.info(
            f"📊 Quality: {overall:.2f} ({'sufficient' if overall > 0.6 else 'insufficient'})"
        )

        return {"quality_assessment": assessment}

    async def check_knowledge(self, state: AgentState) -> Dict[str, Any]:
        """Ask which artists user knows."""
        logger.info("🎤 Tool: Check Knowledge")

        # Handle both dict and Pydantic model
        if isinstance(state, dict):
            state = AgentState(**state)

        candidates = state.candidate_tracks

        # Extract unique artists from top 15 (not 50!)
        artists = list(
            set(
                t.get("artist") if isinstance(t, dict) else t.artist
                for t in candidates[:15]
            )
        )

        options = [{"label": artist, "value": artist} for artist in artists]
        options.append({"label": "None of them", "value": "none"})
        options.append({"label": "All of them", "value": "all"})

        return {
            "knowledge_checked": True,
            "ui_state": {
                "message": "Which of these artists do you know? (Select all that apply)",
                "options": options,
                "cards": [],
                "thought_process": [f"Checking knowledge of {len(artists)} artists"],
            },
        }

    async def present_results(self, state: AgentState) -> Dict[str, Any]:
        """Present final curated playlist."""
        logger.info("🎁 Tool: Present Results")

        # Handle both dict and Pydantic model
        if isinstance(state, dict):
            state = AgentState(**state)

        try:
            candidates = state.candidate_tracks
            known = state.known_artists
            profile = state.playlist_profile or {}
            error = state.error

            # Handle error state
            if error:
                return {
                    "results_presented": True,
                    "ui_state": {
                        "message": f"I encountered an issue: {error}\n\nPlease try again or adjust your preferences.",
                        "options": [],
                        "cards": [],
                        "thought_process": [f"Error: {error}"],
                    },
                }

            # Handle no candidates
            if len(candidates) == 0:
                return {
                    "results_presented": True,
                    "ui_state": {
                        "message": "I couldn't find any tracks matching your criteria. This might mean:\n\n• Your database doesn't have enough tracks yet\n• The vibe constraints were too strict\n\nTry adding more tracks to your library or selecting a different vibe!",
                        "options": [],
                        "cards": [],
                        "thought_process": ["No candidates found"],
                    },
                }

            # Filter unknown artists
            unknown = [
                t
                for t in candidates
                if (t.get("artist") if isinstance(t, dict) else t.artist) not in known
            ]

            # Select top 5 (prioritize unknown, but include known if needed)
            if len(unknown) >= 5:
                final = unknown[:5]
            else:
                final = unknown + candidates[: 5 - len(unknown)]

            # Handle case where we still have no tracks
            if len(final) == 0:
                return {
                    "results_presented": True,
                    "ui_state": {
                        "message": "I couldn't find enough tracks to recommend. Try a different vibe or add more tracks to your library!",
                        "options": [],
                        "cards": [],
                        "thought_process": ["Not enough tracks after filtering"],
                    },
                }

            # Generate pitches with rich audio features (BATCHED for speed - single LLM call!)
            import asyncio
            from pydantic import BaseModel, Field
            from typing import List

            # Step 1: Build context for all tracks
            track_contexts = []
            for t in final:
                # Handle both dict and Pydantic model
                if isinstance(t, dict):
                    t_id = t.get("id")
                    t_title = t.get("title")
                    t_artist = t.get("artist")
                    t_bpm = t.get("bpm")
                    t_energy = t.get("energy")
                    t_brightness = t.get("brightness")
                    t_harmonic_ratio = t.get("harmonic_ratio")
                    t_key = t.get("estimated_key")
                else:
                    t_id = t.id
                    t_title = t.title
                    t_artist = t.artist
                    t_bpm = t.bpm
                    t_energy = t.energy
                    t_brightness = getattr(t, "brightness", None)
                    t_harmonic_ratio = getattr(t, "harmonic_ratio", None)
                    t_key = getattr(t, "estimated_key", None)

                # Build comparative context with ACTUAL NUMBERS as evidence
                comparisons = []

                # Compare BPM (show the numbers!)
                if t_bpm and profile.get("avg_bpm"):
                    avg_bpm = profile["avg_bpm"]
                    if abs(t_bpm - avg_bpm) < 10:
                        comparisons.append(
                            f"its {t_bpm:.0f} BPM perfectly matches your playlist's {avg_bpm:.0f} BPM tempo"
                        )
                    elif t_bpm < avg_bpm:
                        comparisons.append(
                            f"its slower {t_bpm:.0f} BPM (vs your {avg_bpm:.0f}) creates a more relaxed feel"
                        )
                    else:
                        comparisons.append(
                            f"its faster {t_bpm:.0f} BPM (vs your {avg_bpm:.0f}) adds subtle energy"
                        )

                # Compare Energy (show the numbers!)
                if t_energy is not None and profile.get("avg_energy") is not None:
                    avg_energy = profile["avg_energy"]
                    if abs(t_energy - avg_energy) < 0.1:
                        comparisons.append(
                            f"energy level of {t_energy:.2f} closely matches your {avg_energy:.2f}"
                        )
                    elif t_energy < avg_energy:
                        comparisons.append(
                            f"lower energy ({t_energy:.2f} vs {avg_energy:.2f}) maintains the intimate vibe"
                        )
                    else:
                        comparisons.append(
                            f"higher energy ({t_energy:.2f} vs {avg_energy:.2f}) adds dynamic contrast"
                        )

                # Compare Brightness (show the numbers!)
                if t_brightness and profile.get("avg_brightness"):
                    avg_brightness = profile["avg_brightness"]
                    if abs(t_brightness - avg_brightness) < 200:
                        comparisons.append(
                            f"brightness of {t_brightness:.0f} matches your {avg_brightness:.0f} tonal palette"
                        )
                    elif t_brightness < avg_brightness:
                        comparisons.append(
                            f"warmer tones ({t_brightness:.0f} vs {avg_brightness:.0f}) deepen the atmosphere"
                        )
                    else:
                        comparisons.append(
                            f"brighter tones ({t_brightness:.0f} vs {avg_brightness:.0f}) add clarity"
                        )

                # Harmonic ratio (show the numbers!)
                if (
                    t_harmonic_ratio is not None
                    and profile.get("avg_harmonic_ratio") is not None
                ):
                    avg_harmonic = profile["avg_harmonic_ratio"]
                    if abs(t_harmonic_ratio - avg_harmonic) < 0.1:
                        comparisons.append(
                            f"harmonic ratio of {t_harmonic_ratio:.2f} aligns with your {avg_harmonic:.2f}"
                        )
                    elif t_harmonic_ratio > avg_harmonic:
                        comparisons.append(
                            f"richer harmonics ({t_harmonic_ratio:.2f} vs {avg_harmonic:.2f}) add complexity"
                        )

                # Key (always show if available)
                if t_key:
                    comparisons.append(f"composed in {t_key}")

                context = (
                    "; ".join(comparisons) if comparisons else "unique sonic qualities"
                )

                track_contexts.append(
                    {
                        "id": t_id,
                        "title": t_title,
                        "artist": t_artist,
                        "evidence": context,
                    }
                )

            # Step 2: Define structured output for batched pitch generation
            class TrackPitch(BaseModel):
                """Single track pitch."""

                track_index: int = Field(description="Index of the track (0-4)")
                reason: str = Field(
                    description="One compelling sentence explaining why this track is a hidden gem"
                )

            class BatchPitches(BaseModel):
                """All track pitches in one response."""

                pitches: List[TrackPitch] = Field(
                    description="List of pitches, one per track"
                )

            # Step 3: Create batched prompt
            tracks_text = "\n\n".join(
                [
                    f"Track {i}: '{tc['title']}' by {tc['artist']}\nEvidence: {tc['evidence']}"
                    for i, tc in enumerate(track_contexts)
                ]
            )

            batch_prompt = f"""You are a music curator. Write a compelling 1-sentence pitch for EACH of the following tracks.
For each track, use the provided EVIDENCE to justify the recommendation. Be specific about WHY the metrics make it a good match.

{tracks_text}

Provide exactly {len(track_contexts)} pitches, one for each track."""

            # Step 4: Generate all pitches in ONE LLM call
            try:
                batch_result = await self.creative_llm.with_structured_output(
                    BatchPitches
                ).ainvoke(batch_prompt)

                # Map pitches back to tracks
                cards = []
                for i, tc in enumerate(track_contexts):
                    # Find matching pitch by index
                    pitch = next(
                        (p for p in batch_result.pitches if p.track_index == i), None
                    )
                    reason = (
                        pitch.reason
                        if pitch
                        else "A great track that complements your playlist's vibe!"
                    )

                    cards.append(
                        {
                            "id": tc["id"],
                            "title": tc["title"],
                            "artist": tc["artist"],
                            "reason": reason,
                        }
                    )
            except Exception as e:
                logger.error(f"❌ Batch pitch generation failed: {e}", exc_info=True)
                # Fallback to simple reasons
                cards = [
                    {
                        "id": tc["id"],
                        "title": tc["title"],
                        "artist": tc["artist"],
                        "reason": "A great track that complements your playlist's vibe!",
                    }
                    for tc in track_contexts
                ]

            # Generate two-part justification (Understanding + Selection)
            try:
                # Build descriptive profile (not just numbers)
                profile_desc = []

                # Tempo description
                if profile.get("avg_bpm"):
                    bpm = profile["avg_bpm"]
                    if bpm < 90:
                        profile_desc.append("slow, contemplative tempo")
                    elif bpm < 120:
                        profile_desc.append("moderate, relaxed tempo")
                    elif bpm < 140:
                        profile_desc.append("upbeat, energetic tempo")
                    else:
                        profile_desc.append("fast, driving tempo")

                # Energy description
                if profile.get("avg_energy") is not None:
                    energy = profile["avg_energy"]
                    if energy < 0.3:
                        profile_desc.append("low energy, intimate feel")
                    elif energy < 0.6:
                        profile_desc.append("moderate energy, balanced dynamics")
                    else:
                        profile_desc.append("high energy, intense dynamics")

                # Brightness description
                if profile.get("avg_brightness"):
                    brightness = profile["avg_brightness"]
                    if brightness < 1500:
                        profile_desc.append("warm, dark tonal quality")
                    elif brightness < 2000:
                        profile_desc.append("balanced tonal warmth")
                    else:
                        profile_desc.append("bright, vibrant tonal quality")

                # Genres
                if profile.get("top_genres"):
                    profile_desc.append(
                        f"{', '.join(profile['top_genres'][:2])} influences"
                    )

                profile_str = (
                    "; ".join(profile_desc)
                    if profile_desc
                    else "your playlist's unique character"
                )

                # Build track list for context
                track_list = "\n".join(
                    [f"- {c['title']} by {c['artist']}" for c in cards]
                )

                # Generate Understanding and Selection in parallel
                understanding_prompt = ChatPromptTemplate.from_template(
                    "You are analyzing a music playlist with these characteristics: {profile}.\n\n"
                    "Describe what makes this playlist special in 2 sentences. Focus on the VIBE and MOOD. "
                    "Be conversational and warm. Don't mention specific numbers."
                )
                understanding_chain = understanding_prompt | self.creative_llm

                selection_prompt = ChatPromptTemplate.from_template(
                    "You are a music curator. You selected these {count} tracks as hidden gems:\n\n{tracks}\n\n"
                    "The original playlist has: {profile}.\n\n"
                    "Explain in 2-3 sentences WHY you chose these specific tracks and HOW they complement the playlist. "
                    "Be specific about musical qualities (tempo, energy, mood, instrumentation). "
                    "Write as if you're explaining your curation choices to the user."
                )
                selection_chain = selection_prompt | self.reasoning_llm

                # Run both in parallel
                understanding_result, selection_result = await asyncio.gather(
                    understanding_chain.ainvoke({"profile": profile_str}),
                    selection_chain.ainvoke(
                        {
                            "count": len(cards),
                            "tracks": track_list,
                            "profile": profile_str,
                        }
                    ),
                )

                understanding_text = understanding_result.content.strip()
                selection_text = selection_result.content.strip()

                # Add note if user knew all artists
                if len(unknown) == 0 and len(known) > 0:
                    selection_text += " (Note: You knew all the artists I found, so these are the best matches from familiar artists.)"

            except Exception as e:
                logger.error(f"❌ Failed to generate justification: {e}")
                understanding_text = (
                    "Your playlist has a unique character that I've analyzed carefully."
                )
                selection_text = (
                    f"I found {len(cards)} tracks that perfectly complement your vibe!"
                )

            # Combine for fallback message
            message = f"**Understanding:**\n{understanding_text}\n\n**Selection:**\n{selection_text}"

            return {
                "results_presented": True,
                "ui_state": {
                    "message": message,
                    "understanding": understanding_text,
                    "selection": selection_text,
                    "options": [],
                    "cards": cards,
                    "thought_process": [
                        f"Selected {len(cards)} tracks from {len(candidates)} candidates",
                        f"Filtered out {len(known)} known artists",
                    ],
                },
            }
        except Exception as e:
            logger.error(f"❌ present_results failed: {e}", exc_info=True)
            return {
                "results_presented": True,
                "error": str(e),
                "ui_state": {
                    "message": "Sorry, I encountered an error while preparing your recommendations. Please try again.",
                    "options": [],
                    "cards": [],
                    "thought_process": [f"Error: {str(e)}"],
                },
            }
