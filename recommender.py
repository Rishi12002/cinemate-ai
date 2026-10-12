"""
recommender.py - Hybrid Recommendation Engine with Transparent 7-Factor Scoring
CineMate AI - "Your taste. Your next obsession."
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preferences import UserPreferences
from tmdb_client import TMDBClient
from ai_agent import AIAgent

SAMPLE_CATALOGUE_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_catalogue.json")

# Adjustable Transparent Weights
WEIGHT_GENRE = 0.30
WEIGHT_THEME_PLOT = 0.25
WEIGHT_MOOD_TONE = 0.15
WEIGHT_RATING = 0.10
WEIGHT_LANGUAGE_REGION = 0.10
WEIGHT_RELEASE_YEAR = 0.05
WEIGHT_RUNTIME = 0.05


class RecommenderEngine:
    """
    Hybrid recommendation engine combining hard-constraint filtering,
    TF-IDF semantic plot similarity, and multi-factor weighted ranking.
    """

    def __init__(
        self,
        tmdb_client: Optional[TMDBClient] = None,
        ai_agent: Optional[AIAgent] = None,
        sample_path: str = SAMPLE_CATALOGUE_PATH
    ):
        self.tmdb_client = tmdb_client or TMDBClient()
        self.ai_agent = ai_agent or AIAgent()
        self.sample_catalogue = self._load_sample_catalogue(sample_path)

    def _load_sample_catalogue(self, path: str) -> List[Dict[str, Any]]:
        """Load local fallback curated dataset."""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading sample catalogue from {path}: {e}")
        return []

    def is_demo_mode(self) -> bool:
        """Return True if running in offline demo mode using sample catalogue."""
        return not self.tmdb_client.is_configured()

    def get_candidate_pool(self, preferences: UserPreferences) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Fetch candidate pool from TMDB if configured, or from curated sample catalogue.
        Returns (candidates, is_demo_flag).
        """
        if self.tmdb_client.is_configured():
            try:
                # 1. If similar titles mentioned, search for them first
                similar_candidates = []
                for title in preferences.similar_titles[:2]:
                    search_res = self.tmdb_client.search_titles(title, preferences.content_type)
                    if search_res:
                        top_ref = search_res[0]
                        similar_candidates.extend(self.tmdb_client.get_similar(top_ref["id"], top_ref["media_type"]))

                # 2. Discover based on genre/language/year
                discovered = self.tmdb_client.discover_titles(preferences)

                combined = similar_candidates + discovered
                # Deduplicate
                seen = set()
                candidates = []
                for item in combined:
                    key = (item["media_type"], item["id"])
                    if key not in seen:
                        seen.add(key)
                        candidates.append(item)

                if candidates:
                    return candidates, False
            except Exception as e:
                print(f"TMDB query failed ({e}). Falling back to sample catalogue.")

        # Default / Demo Mode candidate pool
        return [dict(x) for x in self.sample_catalogue], True

    def filter_hard_constraints(
        self,
        candidates: List[Dict[str, Any]],
        preferences: UserPreferences
    ) -> List[Dict[str, Any]]:
        """
        Apply strict non-negotiable filters:
        - Content type (Movie vs TV Series)
        - Release year bounds
        - Language / Country requirements
        - Strict content restrictions (e.g., no gore)
        """
        filtered = []

        for item in candidates:
            # 1. Content Type Filter
            if preferences.content_type in ("movie", "tv"):
                if item.get("media_type") != preferences.content_type:
                    continue

            # 2. Release Year Filter
            year = item.get("release_year")
            if year:
                if preferences.min_year and year < preferences.min_year:
                    continue
                if preferences.max_year and year > preferences.max_year:
                    continue

            # 3. Language & Country / Industry Filter
            if preferences.preferred_language:
                lang = item.get("original_language", "").lower()
                req_lang = preferences.preferred_language.lower()
                # If specifically Indian cinema, match common Indian languages (hi, te, kn, ta)
                if preferences.country_or_industry == "India":
                    if lang not in ["hi", "te", "kn", "ta", "ml"] and "IN" not in item.get("origin_country", ""):
                        continue
                elif lang != req_lang:
                    continue

            if preferences.country_or_industry and preferences.country_or_industry != "Hollywood":
                country = item.get("origin_country", "").upper()
                country_map = {"India": "IN", "South Korea": "KR", "Japan": "JP", "UK": "GB", "Germany": "DE"}
                expected_code = country_map.get(preferences.country_or_industry)
                if expected_code and country and country != expected_code:
                    continue

            # 4. Runtime Filter
            if preferences.max_runtime:
                rt = item.get("runtime_minutes")
                if rt and rt > preferences.max_runtime:
                    continue

            # 5. Content Restrictions Filter (e.g. "no gore")
            if "no gore" in preferences.content_restrictions:
                keywords = [k.lower() for k in item.get("keywords", [])]
                overview = item.get("overview", "").lower()
                if "gore" in keywords or "slasher" in keywords or "gory" in overview:
                    continue

            filtered.append(item)

        return filtered

    def calculate_match_scores(
        self,
        candidates: List[Dict[str, Any]],
        preferences: UserPreferences
    ) -> List[Dict[str, Any]]:
        """
        Compute transparent 7-factor composite score for each candidate.
        Weights:
        - Genre Match: 30%
        - Theme & Plot Similarity: 25%
        - Mood & Tone Match: 15%
        - User Rating: 10%
        - Language & Regional Preference: 10%
        - Release Year Preference: 5%
        - Runtime Preference: 5%
        """
        if not candidates:
            return []

        # Prepare Plot & Keyword Corpus for TF-IDF
        query_text = f"{preferences.raw_query} {' '.join(preferences.genres)} {preferences.mood or ''} {' '.join(preferences.tone)}"
        corpus = [query_text]
        for item in candidates:
            item_text = f"{item.get('title', '')} {' '.join(item.get('genres', []))} {item.get('overview', '')} {' '.join(item.get('keywords', []))}"
            corpus.append(item_text)

        # Compute TF-IDF Cosine Similarity
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(corpus)
            cosine_sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        except Exception:
            cosine_sims = np.zeros(len(candidates))

        scored_items = []
        for idx, item in enumerate(candidates):
            # 1. Genre Score (0.0 - 1.0)
            item_genres = [g.lower() for g in item.get("genres", [])]
            if preferences.genres:
                target_genres = [g.lower() for g in preferences.genres]
                intersection = set(item_genres).intersection(target_genres)
                genre_score = len(intersection) / max(1, len(target_genres))
            else:
                genre_score = 0.5  # Neutral if no specific genre requested

            # 2. Theme & Plot Similarity (0.0 - 1.0)
            theme_score = float(cosine_sims[idx]) if idx < len(cosine_sims) else 0.0
            theme_score = min(1.0, max(0.0, theme_score))

            # 3. Mood & Tone Score (0.0 - 1.0)
            mood_score = 0.0
            item_moods = [m.lower() for m in item.get("moods", [])]
            item_keywords = [k.lower() for k in item.get("keywords", [])]
            if preferences.mood:
                if preferences.mood.lower() in item_moods:
                    mood_score += 0.6
                elif any(preferences.mood.lower() in kw for kw in item_keywords):
                    mood_score += 0.4

            if preferences.tone:
                tone_matches = sum(1 for t in preferences.tone if t.lower() in item_moods or any(t.lower() in kw for kw in item_keywords))
                mood_score += min(0.4, 0.2 * tone_matches)
            mood_score = min(1.0, max(0.0, mood_score))

            # 4. User Rating Score (0.0 - 1.0)
            raw_rating = item.get("rating", 0.0) or 0.0
            rating_score = min(1.0, max(0.0, raw_rating / 10.0))

            # 5. Language & Regional Preference Score (0.0 - 1.0)
            lang_score = 0.5
            if preferences.preferred_language or preferences.country_or_industry:
                lang = item.get("original_language", "").lower()
                country = item.get("origin_country", "").upper()
                if preferences.preferred_language and lang == preferences.preferred_language.lower():
                    lang_score = 1.0
                elif preferences.country_or_industry == "India" and (lang in ["hi", "te", "kn", "ta"] or country == "IN"):
                    lang_score = 1.0
                elif preferences.country_or_industry == "South Korea" and (lang == "ko" or country == "KR"):
                    lang_score = 1.0
                else:
                    lang_score = 0.2

            # 6. Release Year Score (0.0 - 1.0)
            year_score = 0.7
            item_year = item.get("release_year")
            if item_year:
                if preferences.min_year and preferences.max_year:
                    if preferences.min_year <= item_year <= preferences.max_year:
                        year_score = 1.0
                    else:
                        diff = min(abs(item_year - preferences.min_year), abs(item_year - preferences.max_year))
                        year_score = max(0.0, 1.0 - (diff * 0.08))
                elif preferences.min_year:
                    if item_year >= preferences.min_year:
                        year_score = 1.0
                    else:
                        year_score = max(0.0, 1.0 - ((preferences.min_year - item_year) * 0.1))
                elif preferences.max_year:
                    if item_year <= preferences.max_year:
                        year_score = 1.0
                    else:
                        year_score = max(0.0, 1.0 - ((item_year - preferences.max_year) * 0.1))

            # 7. Runtime Score (0.0 - 1.0)
            runtime_score = 0.7
            if preferences.max_runtime:
                rt = item.get("runtime_minutes")
                if rt and rt <= preferences.max_runtime:
                    runtime_score = 1.0
                elif rt:
                    runtime_score = max(0.0, 1.0 - ((rt - preferences.max_runtime) / 60.0))

            # Composite Weighted Sum
            composite_score = (
                (WEIGHT_GENRE * genre_score) +
                (WEIGHT_THEME_PLOT * theme_score) +
                (WEIGHT_MOOD_TONE * mood_score) +
                (WEIGHT_RATING * rating_score) +
                (WEIGHT_LANGUAGE_REGION * lang_score) +
                (WEIGHT_RELEASE_YEAR * year_score) +
                (WEIGHT_RUNTIME * runtime_score)
            )

            # Boost if specifically listed in similar titles request
            if preferences.similar_titles:
                title_lower = item.get("title", "").lower()
                if any(st.lower() in title_lower for st in preferences.similar_titles):
                    composite_score = max(0.95, composite_score)

            match_pct = int(round(composite_score * 100))
            match_pct = max(45, min(99, match_pct))  # Normalized UI display bound

            item_copy = dict(item)
            item_copy["composite_score"] = composite_score
            item_copy["match_percentage"] = match_pct
            item_copy["score_breakdown"] = {
                "genre": round(genre_score, 2),
                "theme_plot": round(theme_score, 2),
                "mood_tone": round(mood_score, 2),
                "rating": round(rating_score, 2),
                "language_region": round(lang_score, 2),
                "release_year": round(year_score, 2),
                "runtime": round(runtime_score, 2)
            }
            scored_items.append(item_copy)

        # Sort descending by composite score, tie-break by rating
        scored_items.sort(key=lambda x: (x["composite_score"], x.get("rating", 0.0)), reverse=True)
        return scored_items

    def recommend(
        self,
        user_message: str,
        current_preferences: Optional[UserPreferences] = None
    ) -> Dict[str, Any]:
        """
        End-to-End recommendation pipeline:
        1. Parse user message into UserPreferences
        2. Retrieve Candidate Pool
        3. Apply Hard Constraints
        4. Calculate 7-Factor Weighted Scores
        5. Generate Grounded AI Explanations
        """
        # Step 1: Parse
        prefs = self.ai_agent.parse_request(user_message, current_preferences)

        # Step 2: Fetch Candidates
        candidates, is_demo = self.get_candidate_pool(prefs)

        # Step 3: Hard Filter
        filtered = self.filter_hard_constraints(candidates, prefs)
        relaxation_notice = None

        # Fallback Relaxation if 0 candidates matched hard filters
        if not filtered and candidates:
            relaxation_notice = "Notice: We relaxed strict filters (year or runtime) to present the best matching titles for your taste."
            # Relax year and runtime, keep content_type
            relaxed_prefs = UserPreferences.from_dict(prefs.to_dict())
            relaxed_prefs.min_year = None
            relaxed_prefs.max_year = None
            relaxed_prefs.max_runtime = None
            filtered = self.filter_hard_constraints(candidates, relaxed_prefs)
            if not filtered:
                # Fallback to candidate pool
                filtered = candidates[:10]

        # Step 4: Rank
        ranked = self.calculate_match_scores(filtered, prefs)

        # Take top N
        top_k = prefs.num_recommendations or 5
        recommendations = ranked[:top_k]

        # Step 5: Explanations
        for rec in recommendations:
            rec["ai_explanation"] = self.ai_agent.generate_explanation(rec, prefs)

        return {
            "preferences": prefs,
            "recommendations": recommendations,
            "is_demo_mode": is_demo,
            "relaxation_notice": relaxation_notice,
            "total_matches": len(ranked)
        }

    def get_similar_titles(self, item_id: int, media_type: str = "movie", top_n: int = 4) -> List[Dict[str, Any]]:
        """Find titles similar to a selected item using TMDB or sample TF-IDF."""
        if self.tmdb_client.is_configured():
            sims = self.tmdb_client.get_similar(item_id, media_type)
            if sims:
                return sims[:top_n]

        # Fallback to local similarity search
        target_item = None
        for item in self.sample_catalogue:
            if item.get("id") == item_id:
                target_item = item
                break

        if not target_item and self.sample_catalogue:
            target_item = self.sample_catalogue[0]

        if not target_item:
            return []

        # Vectorize all sample items
        texts = [f"{i.get('title')} {' '.join(i.get('genres', []))} {i.get('overview')} {' '.join(i.get('keywords', []))}" for i in self.sample_catalogue]
        vec = TfidfVectorizer(stop_words='english')
        matrix = vec.fit_transform(texts)

        target_idx = 0
        for idx, i in enumerate(self.sample_catalogue):
            if i.get("id") == target_item.get("id"):
                target_idx = idx
                break

        sim_scores = cosine_similarity(matrix[target_idx:target_idx+1], matrix).flatten()
        similar_indices = sim_scores.argsort()[::-1]

        results = []
        for idx in similar_indices:
            if idx != target_idx:
                results.append(self.sample_catalogue[idx])
            if len(results) >= top_n:
                break

        return results
