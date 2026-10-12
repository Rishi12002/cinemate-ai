"""
tmdb_client.py - Robust Client Service for The Movie Database (TMDB) API
CineMate AI - "Your taste. Your next obsession."
"""

import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

GENRE_MAP_MOVIE = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

GENRE_MAP_TV = {
    10759: "Action & Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 10762: "Kids", 9648: "Mystery",
    10763: "News", 10764: "Reality", 10765: "Sci-Fi & Fantasy", 10766: "Soap",
    10767: "Talk", 10768: "War & Politics", 37: "Western"
}

# Reverse lookup for genre name to ID
GENRE_NAME_TO_ID = {
    "action": 28, "adventure": 12, "animation": 16, "anime": 16,
    "comedy": 35, "crime": 80, "documentary": 99, "drama": 18,
    "family": 10751, "fantasy": 14, "history": 36, "horror": 27,
    "music": 10402, "mystery": 9648, "romance": 10749, "romantic": 10749,
    "science fiction": 878, "sci-fi": 878, "thriller": 53, "war": 10752, "western": 37
}


class TMDBClient:
    """Client for interacting with TMDB REST API with graceful error handling."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TMDB_API_KEY")
        self.session = requests.Session()
        self.timeout = 8.0  # seconds

    def is_configured(self) -> bool:
        """Check if an API key is present."""
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_tmdb_api_key_here")

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Safely execute GET request with timeout and error handling."""
        if not self.is_configured():
            return None

        req_params = params.copy() if params else {}
        req_params["api_key"] = self.api_key

        url = f"{TMDB_BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=req_params, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("TMDB API: Invalid API key (HTTP 401).")
                return None
            elif response.status_code == 429:
                print("TMDB API: Rate limit hit (HTTP 429).")
                return None
            else:
                print(f"TMDB API warning: {url} returned status {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"TMDB network error calling {url}: {e}")
            return None

    def normalize_item(self, raw: Dict[str, Any], default_media_type: str = "movie") -> Dict[str, Any]:
        """Normalize TMDB raw payload into uniform CineMate dictionary format."""
        media_type = raw.get("media_type") or default_media_type
        item_id = raw.get("id")

        # Determine Title
        title = raw.get("title") or raw.get("name") or raw.get("original_title") or "Untitled"

        # Determine Release Year
        date_str = raw.get("release_date") or raw.get("first_air_date") or ""
        release_year = None
        if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
            release_year = int(date_str[:4])

        # Rating and Vote Count
        rating = round(float(raw.get("vote_average", 0.0)), 1)
        vote_count = int(raw.get("vote_count", 0))

        # Genres
        genres = []
        if "genres" in raw and isinstance(raw["genres"], list):
            genres = [g.get("name") for g in raw["genres"] if isinstance(g, dict) and g.get("name")]
        elif "genre_ids" in raw and isinstance(raw["genre_ids"], list):
            genre_map = GENRE_MAP_TV if media_type == "tv" else GENRE_MAP_MOVIE
            genres = [genre_map.get(gid) for gid in raw["genre_ids"] if genre_map.get(gid)]

        # Poster Image
        poster_path = raw.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

        # Runtime or Episode Count
        runtime_or_episodes = "Not available"
        runtime_minutes = None
        if media_type == "movie":
            rt = raw.get("runtime")
            if rt:
                runtime_minutes = rt
                runtime_or_episodes = f"{rt} min"
        else:
            seasons = raw.get("number_of_seasons")
            episodes = raw.get("number_of_episodes")
            if seasons and episodes:
                runtime_or_episodes = f"{seasons} season{'s' if seasons > 1 else ''} ({episodes} eps)"
            elif episodes:
                runtime_or_episodes = f"{episodes} episodes"

        # Origin Country & Language
        original_language = raw.get("original_language", "en")
        origin_country = ""
        countries = raw.get("origin_country") or raw.get("production_countries") or []
        if isinstance(countries, list) and countries:
            first_c = countries[0]
            origin_country = first_c.get("iso_3166_1", "") if isinstance(first_c, dict) else str(first_c)

        overview = raw.get("overview") or "Overview not available."
        tmdb_url = f"https://www.themoviedb.org/{media_type}/{item_id}" if item_id else ""

        return {
            "id": item_id,
            "title": title,
            "media_type": media_type,
            "release_year": release_year,
            "rating": rating,
            "vote_count": vote_count,
            "genres": genres,
            "overview": overview,
            "runtime_minutes": runtime_minutes,
            "runtime_or_episodes": runtime_or_episodes,
            "original_language": original_language,
            "origin_country": origin_country,
            "keywords": raw.get("keywords", []),
            "moods": [],
            "poster_path": poster_url,
            "tmdb_url": tmdb_url,
            "is_demo": False
        }

    def search_titles(self, query: str, media_type: str = "both") -> List[Dict[str, Any]]:
        """Search titles by natural query via TMDB search."""
        if not self.is_configured() or not query.strip():
            return []

        results = []
        if media_type in ("movie", "both"):
            data = self._get("/search/movie", {"query": query, "page": 1})
            if data and "results" in data:
                for item in data["results"][:10]:
                    results.append(self.normalize_item(item, "movie"))

        if media_type in ("tv", "both"):
            data = self._get("/search/tv", {"query": query, "page": 1})
            if data and "results" in data:
                for item in data["results"][:10]:
                    results.append(self.normalize_item(item, "tv"))

        # Deduplicate by (media_type, id)
        seen = set()
        deduped = []
        for r in results:
            key = (r["media_type"], r["id"])
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        return deduped

    def discover_titles(self, preferences: Any) -> List[Dict[str, Any]]:
        """
        Discover titles based on structured user preferences (genres, language, year, rating).
        """
        if not self.is_configured():
            return []

        results = []
        media_types = []
        if preferences.content_type == "movie":
            media_types = ["movie"]
        elif preferences.content_type == "tv":
            media_types = ["tv"]
        else:
            media_types = ["movie", "tv"]

        # Map genre names to TMDB IDs
        genre_ids = []
        for g in preferences.genres:
            gid = GENRE_NAME_TO_ID.get(g.lower())
            if gid:
                genre_ids.append(str(gid))

        for mt in media_types:
            params = {
                "sort_by": "vote_average.desc",
                "vote_count.gte": 100,  # Minimum vote count to avoid obscure noise
                "page": 1
            }

            if genre_ids:
                params["with_genres"] = ",".join(genre_ids)

            if preferences.preferred_language:
                params["with_original_language"] = preferences.preferred_language.lower()

            if preferences.min_rating:
                params["vote_average.gte"] = preferences.min_rating

            if mt == "movie":
                if preferences.min_year:
                    params["primary_release_date.gte"] = f"{preferences.min_year}-01-01"
                if preferences.max_year:
                    params["primary_release_date.lte"] = f"{preferences.max_year}-12-31"
                data = self._get("/discover/movie", params)
            else:
                if preferences.min_year:
                    params["first_air_date.gte"] = f"{preferences.min_year}-01-01"
                if preferences.max_year:
                    params["first_air_date.lte"] = f"{preferences.max_year}-12-31"
                data = self._get("/discover/tv", params)

            if data and "results" in data:
                for item in data["results"][:15]:
                    results.append(self.normalize_item(item, mt))

        return results

    def get_similar(self, item_id: int, media_type: str = "movie") -> List[Dict[str, Any]]:
        """Retrieve similar titles from TMDB for a specific movie or series."""
        if not self.is_configured() or not item_id:
            return []

        endpoint = f"/{media_type}/{item_id}/similar"
        data = self._get(endpoint, {"page": 1})
        if not data or "results" not in data:
            return []

        results = []
        for item in data["results"][:6]:
            results.append(self.normalize_item(item, media_type))
        return results
