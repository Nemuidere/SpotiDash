"""Data processing utilities for the Stats Panel.

This module provides functions to aggregate and transform Spotify data
into statistics-ready formats for visualization.
"""

from datetime import datetime


# =============================================================================
# Listening Time Distribution
# =============================================================================

def extract_listening_time_distribution(recently_played_cache):
    """
    Extract hour-of-day and day-of-week distributions from recently played data.

    Args:
        recently_played_cache: Dict with "items" list of {"track": {...}, "played_at": "ISO8601"}

    Returns:
        Dict with:
        {
            "hour_distribution": {0: 5, 1: 3, ..., 23: 2},  # plays per hour
            "day_distribution": {0: 10, 1: 8, ..., 6: 5}    # plays per day (0=Mon, 6=Sun)
        }
        Or None if no data.
    """
    # Early exit: Invalid or empty input
    if not recently_played_cache or not isinstance(recently_played_cache, dict):
        return None

    items = recently_played_cache.get("items", [])
    if not items:
        return None

    # Initialize distributions with zeros for all hours and days
    hour_distribution = {hour: 0 for hour in range(24)}
    day_distribution = {day: 0 for day in range(7)}

    valid_entries_count = 0

    for entry in items:
        if not isinstance(entry, dict):
            continue

        played_at = entry.get("played_at")
        if not played_at or not isinstance(played_at, str):
            continue

        # Parse ISO8601 timestamp, handling timezone-aware strings
        try:
            timestamp = _parse_iso_timestamp(played_at)
        except (ValueError, TypeError):
            continue

        hour = timestamp.hour
        day = timestamp.weekday()  # Monday=0, Sunday=6

        hour_distribution[hour] += 1
        day_distribution[day] += 1
        valid_entries_count += 1

    # Fail fast: Need at least one valid entry
    if valid_entries_count == 0:
        return None

    return {
        "hour_distribution": hour_distribution,
        "day_distribution": day_distribution,
    }


def _parse_iso_timestamp(timestamp_str):
    """
    Parse an ISO8601 timestamp string into a datetime object.

    Handles timezone-aware strings by normalizing 'Z' suffix to '+00:00'.

    Args:
        timestamp_str: ISO8601 timestamp string (e.g., "2024-01-15T14:30:00Z")

    Returns:
        datetime object with timezone info

    Raises:
        ValueError: If timestamp cannot be parsed
    """
    if not timestamp_str:
        raise ValueError("Empty timestamp string")

    # Normalize 'Z' suffix to '+00:00' for fromisoformat compatibility
    if timestamp_str.endswith("Z"):
        timestamp_str = timestamp_str[:-1] + "+00:00"

    return datetime.fromisoformat(timestamp_str)


# =============================================================================
# Genre Aggregation
# =============================================================================

def aggregate_genres(artists_data):
    """
    Aggregate genre counts from artist data.

    Args:
        artists_data: Dict with "artists" list of artist objects with "genres" field

    Returns:
        List of (genre, count) tuples sorted by count descending, max 10 items.
        Or None if no genres.
    """
    # Early exit: Invalid or empty input
    if not artists_data or not isinstance(artists_data, dict):
        return None

    artists = artists_data.get("artists", [])
    if not artists:
        return None

    genre_counts = {}

    for artist in artists:
        if not isinstance(artist, dict):
            continue

        genres = artist.get("genres", [])
        if not genres or not isinstance(genres, list):
            continue

        for genre in genres:
            if not isinstance(genre, str) or not genre.strip():
                continue

            normalized_genre = genre.strip().lower()
            genre_counts[normalized_genre] = genre_counts.get(normalized_genre, 0) + 1

    # Fail fast: No genres found
    if not genre_counts:
        return None

    # Sort by count descending and take top 10
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_genres[:10]
