"""Vibe matching logic - filter tracks based on vibe preferences."""

import random
from typing import List
from collections import Counter


def filter_by_vibe(tracks: List[dict], vibe_choice: str) -> List[dict]:
    """Filter tracks based on vibe using Spotify audio features.

    Args:
        tracks: List of track dictionaries with audio features
        vibe_choice: User's vibe choice ("Chill", "Energy", or "Surprise")

    Returns:
        Filtered and sorted list of tracks (top 5)
    """
    # Ensure we have tracks with features
    tracks_with_features = [t for t in tracks if t.get("energy") is not None]

    # Fallback if no features available: return random 5
    if not tracks_with_features:
        random.shuffle(tracks)
        return tracks[:5]

    if vibe_choice == "Chill":
        # CHILL: Low Energy (< 0.6)
        # Sort by lowest energy
        filtered = [t for t in tracks_with_features if t["energy"] < 0.6]

        # If too strict, relax threshold
        if len(filtered) < 3:
            filtered = [t for t in tracks_with_features if t["energy"] < 0.75]

        # Sort by lowest energy (most chill)
        filtered.sort(key=lambda x: x["energy"])
        return filtered[:5]

    elif vibe_choice == "Energy":
        # ENERGY: High Energy (> 0.7)
        # Sort by highest energy
        filtered = [t for t in tracks_with_features if t["energy"] > 0.7]

        # If too strict, relax threshold
        if len(filtered) < 3:
            filtered = [t for t in tracks_with_features if t["energy"] > 0.5]

        # Sort by highest energy
        filtered.sort(key=lambda x: x["energy"], reverse=True)
        return filtered[:5]

    # SURPRISE: Random selection
    random.shuffle(tracks)
    return tracks[:5]


def generate_vibe_fun_fact(tracks: List[dict]) -> str:
    """Generate interesting fun facts about the tracks.

    Args:
        tracks: List of track dictionaries with audio features

    Returns:
        Fun fact string to display to user
    """
    fun_facts = []

    # Tempo insights
    tempos = [t.get("bpm") for t in tracks if t.get("bpm")]
    if tempos:
        avg_tempo = sum(tempos) / len(tempos)
        if avg_tempo > 140:
            fun_facts.append(
                f"⚡ Average tempo: {int(avg_tempo)} BPM (perfect for running!)"
            )
        elif avg_tempo > 120:
            fun_facts.append(f"🎵 Average tempo: {int(avg_tempo)} BPM (upbeat)")
        elif avg_tempo < 90:
            fun_facts.append(f"🌙 Average tempo: {int(avg_tempo)} BPM (slow & dreamy)")
        else:
            fun_facts.append(f"🎶 Average tempo: {int(avg_tempo)} BPM (moderate)")

    # Danceability insights
    danceabilities = [t.get("danceability") for t in tracks if t.get("danceability")]
    if danceabilities:
        avg_dance = sum(danceabilities) / len(danceabilities)
        if avg_dance > 0.8:
            fun_facts.append(
                f"💃 Danceability: {int(avg_dance*100)}% - top 10% most danceable!"
            )
        elif avg_dance > 0.6:
            fun_facts.append(
                f"🕺 Danceability: {int(avg_dance*100)}% - these tracks groove"
            )

    # Acousticness insights
    acousticnesses = [t.get("acousticness") for t in tracks if t.get("acousticness")]
    if acousticnesses:
        avg_acoustic = sum(acousticnesses) / len(acousticnesses)
        if avg_acoustic > 0.7:
            fun_facts.append(
                f"🎸 {int(avg_acoustic*100)}% acoustic - raw & organic sound"
            )
        elif avg_acoustic < 0.2:
            fun_facts.append(f"🎹 {int(avg_acoustic*100)}% acoustic - heavily produced")

    # Fallback facts if audio features are missing
    if not fun_facts:
        artists = [t.get("artist") for t in tracks if t.get("artist")]
        if artists:
            featured_artist = random.choice(artists)
            fun_facts.append(f"🎤 Analyzing the discography of {featured_artist}...")

        genres = [t.get("genre") for t in tracks if t.get("genre")]
        if genres:
            most_common = Counter(genres).most_common(1)
            if most_common:
                genre, _ = most_common[0]
                fun_facts.append(f"🎹 Exploring {genre} tracks for you...")

    # Format the fact
    if fun_facts:
        selected_fact = random.choice(fun_facts)
        loading_prefixes = [
            "While I finalize your playlist...",
            "Crunching the numbers...",
            "Just a moment...",
            "Almost there...",
        ]
        prefix = random.choice(loading_prefixes)
        return f"{prefix}\n\n{selected_fact}"

    return "Finalizing your recommendations..."
