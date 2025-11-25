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
    if vibe_choice == "Chill":
        scored_tracks = []
        for t in tracks:
            score = 0
            if t.get("energy") and t["energy"] < 0.5:
                score += 2
            if t.get("acousticness") and t["acousticness"] > 0.5:
                score += 2
            if t.get("bpm") and t["bpm"] < 110:
                score += 1
            if t.get("valence") and t["valence"] < 0.5:
                score += 1
            scored_tracks.append((t, score))
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in scored_tracks[:5]]

    elif vibe_choice == "Energy":
        scored_tracks = []
        for t in tracks:
            score = 0
            if t.get("energy") and t["energy"] > 0.7:
                score += 2
            if t.get("danceability") and t["danceability"] > 0.6:
                score += 2
            if t.get("bpm") and t["bpm"] > 120:
                score += 1
            if t.get("valence") and t["valence"] > 0.6:
                score += 1
            scored_tracks.append((t, score))
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in scored_tracks[:5]]

    # For "Surprise", keep all tracks as is
    return tracks


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
            fun_facts.append(
                f"🌙 Average tempo: {int(avg_tempo)} BPM (slow & dreamy)"
            )
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
            fun_facts.append(
                f"🎹 {int(avg_acoustic*100)}% acoustic - heavily produced"
            )

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
