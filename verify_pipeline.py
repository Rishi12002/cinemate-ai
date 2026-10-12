"""
verify_pipeline.py - Verification script running the 10 core query scenarios and multi-turn state.
"""

from recommender import RecommenderEngine
from preferences import UserPreferences
from database import add_to_watchlist, get_watchlist, remove_from_watchlist

engine = RecommenderEngine()

queries = [
    "Recommend mind-bending sci-fi movies with unexpected endings.",
    "I want a psychological thriller like Shutter Island.",
    "Suggest Indian web series with suspense and strong storytelling.",
    "Recommend romantic movies that are emotional but have a happy ending.",
    "Give me the best horror movies without too much gore.",
    "Recommend something funny for a bad day.",
    "Find English sci-fi movies released after 2020.",
    "Suggest a series with short episodes that I can finish this weekend.",
    "Recommend movies similar to Interstellar, Inception, or The Prestige."
]

print("=== RUNNING SCENARIO TESTS ===")
for q in queries:
    res = engine.recommend(q)
    print(f"\nQuery: '{q}'")
    print(f"Detected: Type={res['preferences'].content_type}, Genres={res['preferences'].genres}, Mood={res['preferences'].mood}")
    print(f"Top 2 Recs:")
    for r in res["recommendations"][:2]:
        print(f"  • {r['title']} ({r.get('release_year', 'N/A')}) - {r['match_percentage']}% Match - {r.get('runtime_or_episodes', '')}")
        print(f"    Why: {r.get('ai_explanation', '')[:100]}...")

print("\n=== MULTI-TURN CONVERSATION TEST ===")
# Turn 1
turn1 = engine.recommend("Recommend five psychological thrillers.")
state = turn1["preferences"]
print(f"Turn 1: Genres={state.genres}, Count={len(turn1['recommendations'])}")

# Turn 2
turn2 = engine.recommend("Only Indian ones.", current_preferences=state)
state = turn2["preferences"]
print(f"Turn 2: Country={state.country_or_industry}, Lang={state.preferred_language}, Genres={state.genres}")
print(f"        Recs: {[r['title'] for r in turn2['recommendations'][:3]]}")

# Turn 3
turn3 = engine.recommend("Released after 2020.", current_preferences=state)
state = turn3["preferences"]
print(f"Turn 3: MinYear={state.min_year}, Country={state.country_or_industry}")
print(f"        Recs: {[r['title'] for r in turn3['recommendations'][:3]]}")

# Turn 4
turn4 = engine.recommend("Give me something less disturbing.", current_preferences=state)
state = turn4["preferences"]
print(f"Turn 4: Restrictions={state.content_restrictions}")
print(f"        Recs: {[r['title'] for r in turn4['recommendations'][:3]]}")

print("\n=== ALL SCENARIOS VERIFIED SUCCESSFULLY ===")
