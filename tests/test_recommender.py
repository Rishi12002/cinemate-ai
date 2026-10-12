"""
test_recommender.py - Tests for recommendation engine, scoring, filtering, database, and fallbacks
"""

import os
import pytest
from recommender import RecommenderEngine
from preferences import UserPreferences
from ai_agent import AIAgent
from database import init_db, add_to_watchlist, remove_from_watchlist, is_in_watchlist, get_watchlist, clear_watchlist

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_watchlist.db")


@pytest.fixture(scope="module")
def engine():
    return RecommenderEngine()


@pytest.fixture(autouse=True)
def clean_db():
    init_db(TEST_DB_PATH)
    clear_watchlist(TEST_DB_PATH)
    yield
    clear_watchlist(TEST_DB_PATH)


def test_genre_matching(engine):
    prefs = UserPreferences(genres=["Science Fiction"])
    candidates, _ = engine.get_candidate_pool(prefs)
    scored = engine.calculate_match_scores(candidates, prefs)
    assert len(scored) > 0
    top = scored[0]
    # Check that top recommendations have Science Fiction
    assert any("Science Fiction" in g for g in top["genres"]) or top["score_breakdown"]["genre"] > 0.5


def test_movie_vs_series_filtering(engine):
    # Test movie filtering
    prefs_movie = UserPreferences(content_type="movie")
    candidates, _ = engine.get_candidate_pool(prefs_movie)
    filtered_movies = engine.filter_hard_constraints(candidates, prefs_movie)
    for m in filtered_movies:
        assert m["media_type"] == "movie"

    # Test TV series filtering
    prefs_tv = UserPreferences(content_type="tv")
    filtered_tv = engine.filter_hard_constraints(candidates, prefs_tv)
    for t in filtered_tv:
        assert t["media_type"] == "tv"


def test_release_year_filtering(engine):
    prefs = UserPreferences(min_year=2020)
    candidates, _ = engine.get_candidate_pool(prefs)
    filtered = engine.filter_hard_constraints(candidates, prefs)
    for item in filtered:
        assert item["release_year"] >= 2020

    prefs_max = UserPreferences(max_year=2015)
    filtered_max = engine.filter_hard_constraints(candidates, prefs_max)
    for item in filtered_max:
        assert item["release_year"] <= 2015


def test_language_and_country_filtering(engine):
    prefs_in = UserPreferences(country_or_industry="India", preferred_language="hi")
    candidates, _ = engine.get_candidate_pool(prefs_in)
    filtered_in = engine.filter_hard_constraints(candidates, prefs_in)
    assert len(filtered_in) > 0
    for item in filtered_in:
        assert item["origin_country"] == "IN" or item["original_language"] in ["hi", "te", "kn", "ta"]


def test_runtime_constraints(engine):
    prefs = UserPreferences(content_type="movie", max_runtime=110)
    candidates, _ = engine.get_candidate_pool(prefs)
    filtered = engine.filter_hard_constraints(candidates, prefs)
    assert len(filtered) > 0
    for item in filtered:
        if item.get("runtime_minutes"):
            assert item["runtime_minutes"] <= 110


def test_scoring_weights_and_normalization(engine):
    prefs = UserPreferences(
        genres=["Science Fiction"],
        mood="mind-bending",
        preferred_language="en",
        raw_query="mind-bending sci-fi"
    )
    candidates, _ = engine.get_candidate_pool(prefs)
    scored = engine.calculate_match_scores(candidates, prefs)
    for item in scored:
        assert 0.0 <= item["composite_score"] <= 1.0
        assert 0 <= item["match_percentage"] <= 100
        # Breakdown components must exist
        for key in ["genre", "theme_plot", "mood_tone", "rating", "language_region", "release_year", "runtime"]:
            assert key in item["score_breakdown"]


def test_empty_results_and_relaxation(engine):
    # Query with contradictory constraints that would yield 0 candidates normally
    res = engine.recommend("Find silent sci-fi series from 1920 under 10 minutes")
    # Engine should auto-relax and return recommendations rather than crashing
    assert "recommendations" in res
    assert len(res["recommendations"]) > 0


def test_missing_metadata_handling(engine):
    # Construct an item with missing fields
    incomplete_item = {
        "id": 999999,
        "title": "Mystery Film",
        "media_type": "movie",
        "release_year": None,
        "rating": None,
        "genres": [],
        "overview": None,
        "runtime_minutes": None
    }
    prefs = UserPreferences(genres=["Drama"])
    scored = engine.calculate_match_scores([incomplete_item], prefs)
    assert len(scored) == 1
    assert scored[0]["composite_score"] >= 0.0


def test_content_restriction_no_gore(engine):
    prefs = UserPreferences(content_restrictions=["no gore"])
    candidates, _ = engine.get_candidate_pool(prefs)
    filtered = engine.filter_hard_constraints(candidates, prefs)
    for item in filtered:
        keywords = [k.lower() for k in item.get("keywords", [])]
        assert "gore" not in keywords
        assert "slasher" not in keywords


def test_watchlist_operations():
    item = {
        "id": 157336,
        "title": "Interstellar",
        "media_type": "movie",
        "release_year": 2014,
        "rating": 8.4,
        "genres": ["Science Fiction", "Drama"],
        "poster_path": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "overview": "Mankind was born on Earth. It was never meant to die here.",
        "tmdb_url": "https://www.themoviedb.org/movie/157336"
    }

    # Verify initially absent
    assert not is_in_watchlist(157336, TEST_DB_PATH)

    # Add to watchlist
    added = add_to_watchlist(item, TEST_DB_PATH)
    assert added is True
    assert is_in_watchlist(157336, TEST_DB_PATH)

    # Duplicate add returns False (ignored)
    added_again = add_to_watchlist(item, TEST_DB_PATH)
    assert added_again is False

    # Get watchlist items
    watchlist = get_watchlist(TEST_DB_PATH)
    assert len(watchlist) == 1
    assert watchlist[0]["title"] == "Interstellar"
    assert watchlist[0]["genres"] == ["Science Fiction", "Drama"]

    # Remove from watchlist
    removed = remove_from_watchlist(157336, TEST_DB_PATH)
    assert removed is True
    assert not is_in_watchlist(157336, TEST_DB_PATH)
    assert len(get_watchlist(TEST_DB_PATH)) == 0


def test_ai_agent_rule_parser():
    agent = AIAgent()
    
    # Test mind-bending sci-fi
    p1 = agent.parse_request("Recommend mind-bending sci-fi movies with unexpected endings.")
    assert p1.content_type == "movie"
    assert "Science Fiction" in p1.genres
    assert p1.mood == "mind-bending"

    # Test Indian web series
    p2 = agent.parse_request("Suggest Indian web series with suspense and strong storytelling.")
    assert p2.content_type == "tv"
    assert p2.country_or_industry == "India"
    assert p2.preferred_language == "hi"

    # Test short series weekend
    p3 = agent.parse_request("Suggest a series with short episodes that I can finish this weekend.")
    assert p3.content_type == "tv"
    assert p3.max_runtime == 60

    # Test English sci-fi after 2020
    p4 = agent.parse_request("Find English sci-fi movies released after 2020.")
    assert p4.content_type == "movie"
    assert "Science Fiction" in p4.genres
    assert p4.min_year == 2020
    assert p4.preferred_language == "en"
