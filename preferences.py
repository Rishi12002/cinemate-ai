"""
preferences.py - Structured User Preference Models & Multi-Turn Context Manager
CineMate AI - "Your taste. Your next obsession."
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class UserPreferences:
    """
    Structured representation of user taste, constraints, and recommendations request.
    Maintains state across multi-turn conversational interactions.
    """
    content_type: str = "both"  # "movie", "tv", or "both"
    genres: List[str] = field(default_factory=list)
    mood: Optional[str] = None  # e.g., "mind-bending", "uplifting", "dark"
    preferred_language: Optional[str] = None  # e.g., "en", "hi", "ko", "ja", "de"
    country_or_industry: Optional[str] = None  # e.g., "India", "Bollywood", "Hollywood", "South Korea"
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_runtime: Optional[int] = None  # in minutes
    max_runtime: Optional[int] = None  # in minutes
    min_rating: Optional[float] = None  # e.g., 7.0
    preferred_streaming: Optional[str] = None  # e.g., "Netflix", "Prime"
    tone: List[str] = field(default_factory=list)  # e.g., ["dark", "funny", "emotional"]
    similar_titles: List[str] = field(default_factory=list)  # reference titles mentioned
    content_restrictions: List[str] = field(default_factory=list)  # e.g., ["no gore", "no violence"]
    num_recommendations: int = 5
    follow_up_question: Optional[str] = None
    raw_query: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Instantiate preferences from dictionary safely handling missing keys."""
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def update_from(self, new_prefs: "UserPreferences") -> "UserPreferences":
        """
        Incrementally merge new preferences from a follow-up query into existing preferences.
        Preserves established taste constraints unless explicitly overwritten.

        Example:
            Turn 1: "5 psychological thrillers" -> genres=['Thriller', 'Mystery']
            Turn 2: "Only Indian ones" -> country='India', language='hi' (genres preserved)
            Turn 3: "Released after 2020" -> min_year=2020 (genres and country preserved)
            Turn 4: "Give me something less disturbing" -> content_restrictions updated
        """
        # Content type: update if new_prefs has an explicit specific type ("movie" or "tv")
        if new_prefs.content_type in ("movie", "tv"):
            self.content_type = new_prefs.content_type

        # Genres: merge unique genres, or overwrite if new ones specifically requested
        if new_prefs.genres:
            # If user explicitly specified different genres, union them
            combined_genres = list(dict.fromkeys(self.genres + new_prefs.genres))
            self.genres = combined_genres

        # Mood & Tone
        if new_prefs.mood:
            self.mood = new_prefs.mood
        if new_prefs.tone:
            self.tone = list(dict.fromkeys(self.tone + new_prefs.tone))

        # Language and Country / Industry
        if new_prefs.preferred_language:
            self.preferred_language = new_prefs.preferred_language
        if new_prefs.country_or_industry:
            self.country_or_industry = new_prefs.country_or_industry

        # Year bounds
        if new_prefs.min_year is not None:
            self.min_year = new_prefs.min_year
        if new_prefs.max_year is not None:
            self.max_year = new_prefs.max_year

        # Runtime bounds
        if new_prefs.min_runtime is not None:
            self.min_runtime = new_prefs.min_runtime
        if new_prefs.max_runtime is not None:
            self.max_runtime = new_prefs.max_runtime

        # Minimum rating
        if new_prefs.min_rating is not None:
            self.min_rating = new_prefs.min_rating

        # Streaming preference
        if new_prefs.preferred_streaming:
            self.preferred_streaming = new_prefs.preferred_streaming

        # Similar reference titles
        if new_prefs.similar_titles:
            self.similar_titles = list(dict.fromkeys(self.similar_titles + new_prefs.similar_titles))

        # Content restrictions (e.g., no gore, less disturbing)
        if new_prefs.content_restrictions:
            self.content_restrictions = list(dict.fromkeys(self.content_restrictions + new_prefs.content_restrictions))

        # Count requested
        if new_prefs.num_recommendations and new_prefs.num_recommendations != 5:
            self.num_recommendations = new_prefs.num_recommendations

        self.follow_up_question = new_prefs.follow_up_question
        self.raw_query = new_prefs.raw_query or self.raw_query

        return self

    def summary_chips(self) -> List[str]:
        """Return clean badge-friendly summary strings of active constraints."""
        chips = []
        if self.content_type == "movie":
            chips.append("🎬 Movies only")
        elif self.content_type == "tv":
            chips.append("📺 TV Series only")
        else:
            chips.append("🎬📺 Movies & Series")

        if self.genres:
            chips.append(f"🎭 {', '.join(self.genres[:3])}")
        if self.country_or_industry:
            chips.append(f"🌍 {self.country_or_industry}")
        elif self.preferred_language:
            chips.append(f"🗣️ Lang: {self.preferred_language.upper()}")

        if self.min_year and self.max_year:
            chips.append(f"📅 {self.min_year}–{self.max_year}")
        elif self.min_year:
            chips.append(f"📅 {self.min_year}+")
        elif self.max_year:
            chips.append(f"📅 Pre-{self.max_year}")

        if self.max_runtime:
            chips.append(f"⏱️ <{self.max_runtime} min")

        if self.min_rating:
            chips.append(f"★ {self.min_rating}+")

        if self.mood:
            chips.append(f"✨ Mood: {self.mood}")

        if self.similar_titles:
            chips.append(f"🔗 Like: {', '.join(self.similar_titles[:2])}")

        if self.content_restrictions:
            chips.append(f"🛡️ {', '.join(self.content_restrictions[:2])}")

        return chips
