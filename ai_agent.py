"""
ai_agent.py - Conversational AI Agent with Gemini GenAI SDK and Rule-based Fallback
CineMate AI - "Your taste. Your next obsession."
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from preferences import UserPreferences

load_dotenv()


class AIAgent:
    """
    Intelligent conversational agent that interprets user requests into structured
    preferences and produces grounded, spoiler-free explanations.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self._init_genai_client()

    def _init_genai_client(self):
        """Initialize the Google GenAI SDK client if credentials are provided."""
        if self.api_key and self.api_key.strip() and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning initializing Google GenAI client: {e}")
                self.client = None

    def is_live(self) -> bool:
        """Return True if a live Gemini client is ready."""
        return self.client is not None

    def parse_request(
        self,
        user_message: str,
        current_preferences: Optional[UserPreferences] = None
    ) -> UserPreferences:
        """
        Parse user natural language into structured UserPreferences.
        Uses Gemini GenAI when available; falls back to robust NLP pattern matcher.
        """
        if self.is_live():
            try:
                return self._parse_with_gemini(user_message, current_preferences)
            except Exception as e:
                print(f"Gemini API parsing failed ({e}), using rule-based fallback.")

        # Fallback NLP rule-based parser
        return self._parse_with_rules(user_message, current_preferences)

    def _parse_with_gemini(
        self,
        user_message: str,
        current_preferences: Optional[UserPreferences] = None
    ) -> UserPreferences:
        """Call Gemini to extract structured JSON matching UserPreferences schema."""
        current_context = ""
        if current_preferences:
            current_context = f"Current active preferences: {json.dumps(current_preferences.to_dict())}\n"

        prompt = f"""
You are the brain of CineMate AI, an expert movie and series recommendation assistant.
Analyze the user's natural language request and convert it into structured JSON.
{current_context}
User request: "{user_message}"

Respond ONLY with a valid JSON object matching these fields:
{{
  "content_type": "movie" | "tv" | "both",
  "genres": ["Genre1", "Genre2"],
  "mood": "mind-bending" | "uplifting" | "dark" | "intense" | "funny" | "romantic" | "wholesome" | null,
  "preferred_language": "en" | "hi" | "ko" | "ja" | "es" | "de" | null,
  "country_or_industry": "India" | "Hollywood" | "South Korea" | "Japan" | "UK" | null,
  "min_year": integer or null,
  "max_year": integer or null,
  "min_runtime": integer or null,
  "max_runtime": integer or null,
  "min_rating": float or null,
  "preferred_streaming": string or null,
  "tone": ["dark", "mind-bending", "humorous"],
  "similar_titles": ["Interstellar", "Inception"],
  "content_restrictions": ["no gore", "no excessive violence"],
  "num_recommendations": 5,
  "follow_up_question": string or null
}}

If the user is asking a follow-up that refines the current preferences (e.g. "Only Indian ones", "Released after 2020", "Give me something less disturbing"), integrate or adjust the fields accordingly.
Do NOT output markdown code fences or conversational text, output only the JSON object.
"""
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text.strip()
        # Strip potential markdown formatting ```json ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

        data = json.loads(text)
        new_prefs = UserPreferences.from_dict(data)
        new_prefs.raw_query = user_message

        if current_preferences:
            # Merge with history
            return current_preferences.update_from(new_prefs)
        return new_prefs

    def _parse_with_rules(
        self,
        text: str,
        current_preferences: Optional[UserPreferences] = None
    ) -> UserPreferences:
        """
        Comprehensive rule-based NLP parser handling genres, media types,
        years, languages, moods, restrictions, similar titles, and follow-ups.
        """
        low = text.lower()
        prefs = UserPreferences(raw_query=text)

        # 1. Content Type Detection
        has_tv = bool(re.search(r'\b(series|tv|shows?|web series|seasons?|episodes?|binge)\b', low))
        has_movie = bool(re.search(r'\b(movies?|films?|cinemas?)\b', low))

        if has_tv and not has_movie:
            prefs.content_type = "tv"
        elif has_movie and not has_tv:
            prefs.content_type = "movie"
        else:
            prefs.content_type = "both"

        # 2. Genre Extraction
        genre_patterns = {
            "Science Fiction": [r'sci-fi', r'science fiction', r'space', r'multiverse', r'cyberpunk', r'time travel'],
            "Thriller": [r'thriller', r'suspense', r'cat and mouse'],
            "Mystery": [r'mystery', r'whodunit', r'detective', r'puzzle'],
            "Psychological": [r'psychological', r'psychological thriller'],
            "Crime": [r'crime', r'mafia', r'gangster', r'heist', r'underworld', r'serial killer', r'police'],
            "Romance": [r'romance', r'romantic', r'love', r'rom-com'],
            "Comedy": [r'comedy', r'funny', r'humor', r'laugh', r'hilarious', r'satire'],
            "Horror": [r'horror', r'scary', r'spooky', r'creepy'],
            "Drama": [r'drama', r'emotional', r'heartfelt'],
            "Action": [r'action', r'adventure', r'fight', r'superhero'],
            "Fantasy": [r'fantasy', r'magic', r'mythology'],
            "Animation": [r'animation', r'anime', r'animated', r'ghibli']
        }
        extracted_genres = []
        for g_name, patterns in genre_patterns.items():
            if any(re.search(pat, low) for pat in patterns):
                extracted_genres.append(g_name)
        prefs.genres = extracted_genres

        # 3. Mood & Tone
        tone_list = []
        if re.search(r'mind-bending|mind bending|twist ending|unexpected ending|matrix', low):
            prefs.mood = "mind-bending"
            tone_list.extend(["mind-bending", "intellectual"])
        elif re.search(r'bad day|comfort|feel[- ]good|happy|wholesome', low):
            prefs.mood = "uplifting"
            tone_list.extend(["funny", "heartwarming"])
        elif re.search(r'dark|gritty|chilling|disturbing', low):
            prefs.mood = "dark"
            tone_list.append("dark")
        elif re.search(r'emotional|cry|touching|heartwarming', low):
            prefs.mood = "emotional"
            tone_list.append("emotional")
        prefs.tone = tone_list

        # 4. Language & Regional/Country Preferences
        if re.search(r'\b(indian|india|bollywood|hindi)\b', low):
            prefs.country_or_industry = "India"
            prefs.preferred_language = "hi"
        elif re.search(r'\b(korean|korea|k-drama|kdrama)\b', low):
            prefs.country_or_industry = "South Korea"
            prefs.preferred_language = "ko"
        elif re.search(r'\b(japanese|japan|anime)\b', low):
            prefs.country_or_industry = "Japan"
            prefs.preferred_language = "ja"
        elif re.search(r'\b(english|hollywood|american|british)\b', low):
            prefs.country_or_industry = "Hollywood"
            prefs.preferred_language = "en"
        elif re.search(r'\b(german|germany)\b', low):
            prefs.preferred_language = "de"

        # 5. Year Filtering
        year_after = re.search(r'(?:after|since|post|from|newer than)\s+(20\d\d|19\d\d)', low)
        year_before = re.search(r'(?:before|prior to|older than)\s+(20\d\d|19\d\d)', low)
        exact_year = re.search(r'\b(20[0-2][0-9]|19[8-9][0-9])\b', low)

        if year_after:
            prefs.min_year = int(year_after.group(1))
        elif year_before:
            prefs.max_year = int(year_before.group(1))
        elif exact_year and not any(k in low for k in ['top', 'top 20']):
            # If standalone year mentioned
            prefs.min_year = int(exact_year.group(1))

        # 6. Runtime & Short Episodes / Weekend binge
        if re.search(r'short episodes|short series|finish this weekend|weekend binge|quick watch', low):
            prefs.content_type = "tv"
            prefs.max_runtime = 60
            prefs.mood = prefs.mood or "bingeable"
        elif re.search(r'under\s+(\d+)\s*(?:min|mins|minutes)', low):
            m = re.search(r'under\s+(\d+)\s*(?:min|mins|minutes)', low)
            prefs.max_runtime = int(m.group(1))

        # 7. Similar Titles Extraction ("like Shutter Island", "similar to Interstellar")
        similar_match = re.search(r'(?:like|similar to|in the vein of)\s+([a-zA-Z0-9\s,]+?)(?:\.|$|and\s+give|released|only)', low)
        if similar_match:
            raw_titles = similar_match.group(1).strip()
            # Split by comma or 'or'
            titles = [t.strip().title() for t in re.split(r'[,|or|and]+', raw_titles) if len(t.strip()) > 2]
            prefs.similar_titles = titles

        # 8. Content Restrictions
        if re.search(r'no gore|without (?:too much )?gore|low gore|not too gory', low):
            prefs.content_restrictions.append("no gore")
        if re.search(r'less disturbing|not (?:too )?disturbing', low):
            prefs.content_restrictions.append("less disturbing")
        if re.search(r'happy ending', low):
            prefs.content_restrictions.append("happy ending")

        # 9. Number of recommendations
        count_match = re.search(r'\b(one|two|three|four|five|six|seven|eight|nine|ten|[1-9]|10)\b\s+(?:recommendations|titles|movies|shows|series)', low)
        word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        if count_match:
            val = count_match.group(1)
            prefs.num_recommendations = word_to_num.get(val, int(val) if val.isdigit() else 5)

        # Merge with existing conversational state if applicable
        if current_preferences:
            return current_preferences.update_from(prefs)
        return prefs

    def generate_explanation(self, item: Dict[str, Any], preferences: UserPreferences) -> str:
        """
        Generate a concise, grounded 'Why this matches you' explanation.
        Highlights genre match, tone, and specific user preferences without spoilers.
        """
        title = item.get("title", "This title")
        genres = item.get("genres", [])
        genre_str = ", ".join(genres[:2]) if genres else "compelling"
        media_label = "movie" if item.get("media_type") == "movie" else "series"

        # Check matched aspects
        reasons = []

        if preferences.mood and preferences.mood.lower() in [m.lower() for m in item.get("moods", [])]:
            reasons.append(f"its {preferences.mood} tone")
        elif preferences.mood:
            reasons.append(f"fitting your requested {preferences.mood} mood")

        # Check genres match
        matched_genres = [g for g in genres if g in preferences.genres]
        if matched_genres:
            reasons.append(f"strong {', '.join(matched_genres[:2])} elements")

        # Check country / language
        if preferences.country_or_industry and (
            preferences.country_or_industry.lower() in item.get("origin_country", "").lower() or
            (preferences.country_or_industry == "India" and item.get("original_language") in ["hi", "te", "kn", "ta"])
        ):
            reasons.append(f"being a premier {preferences.country_or_industry} production")

        # Check similar titles
        if preferences.similar_titles:
            ref_str = ", ".join(preferences.similar_titles[:2])
            reasons.append(f"sharing thematic parallels with {ref_str}")

        # Check restrictions (e.g., no gore)
        if "no gore" in preferences.content_restrictions and ("Horror" in genres or "Thriller" in genres):
            reasons.append("relying on psychological tension rather than graphic gore")

        # Check happy ending
        if "happy ending" in preferences.content_restrictions and "Romance" in genres:
            reasons.append("delivering an emotional journey with an uplifting payoff")

        if not reasons:
            reasons.append(f"its acclaimed rating ({item.get('rating', 'Verified')}/10) and narrative depth")

        reason_summary = " and ".join(reasons[:2])
        return (
            f"Recommended because you asked for {preferences.raw_query.strip() or 'great titles'}. "
            f"This acclaimed {genre_str.lower()} {media_label} matches your taste through {reason_summary}."
        )
