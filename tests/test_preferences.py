"""
test_preferences.py - Unit tests for UserPreferences and multi-turn context updates
"""

import pytest
from preferences import UserPreferences


def test_preferences_defaults():
    prefs = UserPreferences()
    assert prefs.content_type == "both"
    assert prefs.genres == []
    assert prefs.mood is None
    assert prefs.preferred_language is None
    assert prefs.country_or_industry is None
    assert prefs.min_year is None
    assert prefs.max_year is None
    assert prefs.num_recommendations == 5
    assert prefs.content_restrictions == []


def test_preferences_serialization():
    prefs = UserPreferences(
        content_type="movie",
        genres=["Science Fiction", "Thriller"],
        mood="mind-bending",
        min_year=2015,
        num_recommendations=3
    )
    data = prefs.to_dict()
    assert data["content_type"] == "movie"
    assert "Science Fiction" in data["genres"]

    restored = UserPreferences.from_dict(data)
    assert restored.content_type == "movie"
    assert restored.genres == ["Science Fiction", "Thriller"]
    assert restored.mood == "mind-bending"
    assert restored.min_year == 2015
    assert restored.num_recommendations == 3


def test_multi_turn_preference_updates():
    """
    Test the key conversational multi-turn scenario:
    Turn 1: "Recommend five psychological thrillers."
    Turn 2: "Only Indian ones."
    Turn 3: "Released after 2020."
    Turn 4: "Give me something less disturbing."
    """
    # Turn 1
    t1 = UserPreferences(
        content_type="both",
        genres=["Thriller", "Mystery"],
        mood="psychological",
        num_recommendations=5,
        raw_query="Recommend five psychological thrillers."
    )

    # Turn 2: "Only Indian ones"
    t2 = UserPreferences(
        country_or_industry="India",
        preferred_language="hi",
        raw_query="Only Indian ones"
    )
    state = t1.update_from(t2)
    assert state.genres == ["Thriller", "Mystery"]  # Preserved!
    assert state.mood == "psychological"           # Preserved!
    assert state.country_or_industry == "India"     # Added!
    assert state.preferred_language == "hi"         # Added!

    # Turn 3: "Released after 2020"
    t3 = UserPreferences(
        min_year=2020,
        raw_query="Released after 2020"
    )
    state = state.update_from(t3)
    assert state.genres == ["Thriller", "Mystery"]  # Still preserved
    assert state.country_or_industry == "India"     # Still preserved
    assert state.min_year == 2020                   # Added!

    # Turn 4: "Give me something less disturbing"
    t4 = UserPreferences(
        content_restrictions=["less disturbing"],
        raw_query="Give me something less disturbing"
    )
    state = state.update_from(t4)
    assert state.genres == ["Thriller", "Mystery"]  # Preserved
    assert state.country_or_industry == "India"     # Preserved
    assert state.min_year == 2020                   # Preserved
    assert "less disturbing" in state.content_restrictions  # Added!


def test_summary_chips():
    prefs = UserPreferences(
        content_type="movie",
        genres=["Science Fiction"],
        country_or_industry="India",
        min_year=2020,
        mood="mind-bending"
    )
    chips = prefs.summary_chips()
    assert any("Movies only" in c for c in chips)
    assert any("Science Fiction" in c for c in chips)
    assert any("India" in c for c in chips)
    assert any("2020+" in c for c in chips)
    assert any("mind-bending" in c for c in chips)
