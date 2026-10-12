"""
app.py - CineMate AI: Intelligent Movie & Web Series Recommendation Agent
"Your taste. Your next obsession."
"""

import streamlit as st
import os
import json
from dotenv import load_dotenv

from preferences import UserPreferences
from tmdb_client import TMDBClient
from ai_agent import AIAgent
from recommender import RecommenderEngine
from database import (
    init_db,
    add_to_watchlist,
    remove_from_watchlist,
    is_in_watchlist,
    get_watchlist
)

load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="CineMate AI — Movie & Web Series Recommendations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Streaming Theme CSS
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #e2e8f0;
}

/* Background */
.stApp {
    background-color: #0b0f17;
    background-image: radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                      radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.10) 0px, transparent 50%);
}

/* Header Styles */
.hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 70%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}

.hero-tagline {
    font-size: 1.15rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
    font-weight: 400;
}

/* Status Badges */
.status-pill-demo {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(168, 85, 247, 0.15);
    border: 1px solid rgba(168, 85, 247, 0.35);
    color: #c084fc;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 500;
    margin-bottom: 1rem;
}

.status-pill-live {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.35);
    color: #4ade80;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 500;
    margin-bottom: 1rem;
}

/* Card Styling */
.movie-card {
    background: #131926;
    border: 1px solid #1e293b;
    border-radius: 14px;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease;
    display: flex;
    flex-direction: column;
    height: 100%;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.movie-card:hover {
    transform: translateY(-4px);
    border-color: #6366f1;
}

.card-content {
    padding: 1.1rem;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}

.card-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 0.35rem;
    line-height: 1.3;
}

.card-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    font-size: 0.82rem;
    color: #94a3b8;
    margin-bottom: 0.65rem;
}

.badge-type {
    background: #27272a;
    color: #e4e4e7;
    padding: 2px 7px;
    border-radius: 5px;
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
}

.badge-rating {
    background: rgba(234, 179, 8, 0.15);
    color: #facc15;
    padding: 2px 7px;
    border-radius: 5px;
    font-weight: 600;
    font-size: 0.75rem;
}

.badge-match {
    background: rgba(99, 102, 241, 0.2);
    color: #818cf8;
    padding: 2px 7px;
    border-radius: 5px;
    font-weight: 600;
    font-size: 0.75rem;
}

.genre-chip {
    display: inline-block;
    background: #1e293b;
    color: #cbd5e1;
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 12px;
    margin-right: 4px;
    margin-bottom: 4px;
}

.card-overview {
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.45;
    margin-bottom: 0.85rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.why-match-box {
    background: rgba(99, 102, 241, 0.08);
    border-left: 3px solid #6366f1;
    padding: 0.65rem 0.8rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.82rem;
    color: #c7d2fe;
    margin-top: auto;
    margin-bottom: 0.85rem;
    line-height: 1.4;
}

.taste-chip {
    display: inline-flex;
    align-items: center;
    background: #1e293b;
    border: 1px solid #334155;
    color: #cbd5e1;
    font-size: 0.8rem;
    padding: 4px 10px;
    border-radius: 16px;
    margin-right: 6px;
    margin-bottom: 6px;
}

/* Prompt Quick Buttons */
.stButton button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}

/* Image fallback container */
.poster-placeholder {
    height: 340px;
    background: linear-gradient(135deg, #1e293b, #0f172a);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #64748b;
    font-size: 0.9rem;
    text-align: center;
    padding: 1rem;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Initialize Database & Services
@st.cache_resource
def get_engine():
    init_db()
    tmdb_client = TMDBClient()
    ai_agent = AIAgent()
    return RecommenderEngine(tmdb_client=tmdb_client, ai_agent=ai_agent)


engine = get_engine()

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "active_preferences" not in st.session_state:
    st.session_state.active_preferences = UserPreferences()
if "last_recommendations" not in st.session_state:
    st.session_state.last_recommendations = []
if "watchlist_refresh" not in st.session_state:
    st.session_state.watchlist_refresh = 0
if "input_query" not in st.session_state:
    st.session_state.input_query = ""


# Sidebar
with st.sidebar:
    st.markdown("### 🎛️ Taste & Search Filters")
    st.caption("Filters interact seamlessly with your conversational queries.")

    # Content Type Filter
    content_type_choice = st.radio(
        "Content Type",
        options=["Both", "Movies Only", "TV Series Only"],
        index=0 if st.session_state.active_preferences.content_type == "both"
        else (1 if st.session_state.active_preferences.content_type == "movie" else 2)
    )
    if content_type_choice == "Movies Only":
        st.session_state.active_preferences.content_type = "movie"
    elif content_type_choice == "TV Series Only":
        st.session_state.active_preferences.content_type = "tv"
    else:
        st.session_state.active_preferences.content_type = "both"

    # Genre Multiselect
    all_genres = [
        "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
        "Drama", "Family", "Fantasy", "History", "Horror", "Mystery",
        "Romance", "Science Fiction", "Thriller"
    ]
    selected_genres = st.multiselect(
        "Preferred Genres",
        options=all_genres,
        default=[g for g in st.session_state.active_preferences.genres if g in all_genres]
    )
    st.session_state.active_preferences.genres = selected_genres

    # Rating Slider
    min_rating = st.slider("Minimum TMDB Rating", min_value=0.0, max_value=9.5, value=float(st.session_state.active_preferences.min_rating or 6.5), step=0.5)
    st.session_state.active_preferences.min_rating = min_rating if min_rating > 0.0 else None

    # Year Range
    year_range = st.slider("Release Year Range", min_value=1980, max_value=2026, value=(1990, 2026))
    st.session_state.active_preferences.min_year = year_range[0]
    st.session_state.active_preferences.max_year = year_range[1]

    # Max Runtime Slider
    max_runtime = st.slider("Max Movie Runtime (Minutes)", min_value=60, max_value=240, value=180, step=15)
    st.session_state.active_preferences.max_runtime = max_runtime if max_runtime < 240 else None

    # Reset Taste Profile Button
    st.divider()
    if st.button("🔄 Reset Taste Profile", use_container_width=True):
        st.session_state.active_preferences = UserPreferences()
        st.session_state.chat_history = []
        st.session_state.last_recommendations = []
        st.rerun()

    # Engine Status Info
    st.divider()
    st.markdown("#### ⚡ System Status")
    if engine.is_demo_mode():
        st.markdown(
            """
            <div class="status-pill-demo">
                <span>🟣</span> <strong>Demo Mode (Curated Catalogue)</strong>
            </div>
            <p style='font-size: 0.78rem; color: #94a3b8;'>
            Using verified 45+ title catalogue spanning Hollywood, Indian Cinema, K-Dramas & Anime. Set <code>TMDB_API_KEY</code> & <code>GEMINI_API_KEY</code> in <code>.env</code> for live lookups.
            </p>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="status-pill-live">
                <span>🟢</span> <strong>Live TMDB & Gemini Active</strong>
            </div>
            <p style='font-size: 0.78rem; color: #94a3b8;'>
            Connected to TMDB API and Google Gemini GenAI SDK.
            </p>
            """,
            unsafe_allow_html=True
        )

    # Watchlist Count
    current_watchlist = get_watchlist()
    st.markdown(f"**📌 Saved in Watchlist:** `{len(current_watchlist)} titles`")


# Main Area
tab_discover, tab_watchlist = st.tabs(["✨ Discover & Recommend", f"🔖 Watchlist ({len(get_watchlist())})"])

with tab_discover:
    # Hero Title
    st.markdown('<div class="hero-title">CineMate AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-tagline">Your taste. Your next obsession.</div>', unsafe_allow_html=True)

    # Active Preference Memory Chips
    chips = st.session_state.active_preferences.summary_chips()
    if chips:
        st.markdown("**Active Memory Profile:**")
        chips_html = "".join([f'<span class="taste-chip">{c}</span>' for c in chips])
        st.markdown(f"<div>{chips_html}</div>", unsafe_allow_html=True)
        st.caption("CineMate retains your established preferences across follow-up queries (e.g. *'Only Indian ones'* or *'Released after 2020'*).")

    # Sample Quick Prompt Inspirations
    st.markdown("<div style='margin-top: 1rem; margin-bottom: 0.4rem; font-size: 0.88rem; color: #cbd5e1;'>💡 <strong>Try asking or click a prompt:</strong></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌌 Mind-bending sci-fi with twist endings", use_container_width=True):
            st.session_state.input_query = "Recommend mind-bending sci-fi movies with unexpected endings."
        if st.button("🕵️ Psychological thriller like Shutter Island", use_container_width=True):
            st.session_state.input_query = "I want a psychological thriller like Shutter Island."
        if st.button("⚡ English sci-fi released after 2020", use_container_width=True):
            st.session_state.input_query = "Find English sci-fi movies released after 2020."
    with col2:
        if st.button("🎭 Indian crime web series with suspense", use_container_width=True):
            st.session_state.input_query = "Suggest Indian web series with suspense and strong storytelling."
        if st.button("❤️ Emotional romance with happy ending", use_container_width=True):
            st.session_state.input_query = "Recommend romantic movies that are emotional but have a happy ending."
        if st.button("🍿 Short series to binge this weekend", use_container_width=True):
            st.session_state.input_query = "Suggest a series with short episodes that I can finish this weekend."
    with col3:
        if st.button("🤫 Great horror without too much gore", use_container_width=True):
            st.session_state.input_query = "Give me the best horror movies without too much gore."
        if st.button("😄 Something funny for a bad day", use_container_width=True):
            st.session_state.input_query = "Recommend something funny for a bad day."
        if st.button("🪐 Similar to Interstellar & Inception", use_container_width=True):
            st.session_state.input_query = "Recommend movies similar to Interstellar, Inception, or The Prestige."

    # Conversational Search Input
    user_query = st.chat_input("Ask CineMate AI (e.g. 'Recommend 5 psychological thrillers', 'Only Indian ones', etc.)...")

    # If clicked quick prompt
    if st.session_state.input_query and not user_query:
        user_query = st.session_state.input_query
        st.session_state.input_query = ""

    # Execution Flow
    if user_query:
        with st.spinner("Analyzing request and ranking recommendations..."):
            result = engine.recommend(
                user_message=user_query,
                current_preferences=st.session_state.active_preferences
            )
            st.session_state.active_preferences = result["preferences"]
            st.session_state.last_recommendations = result["recommendations"]

            # Save to chat history
            st.session_state.chat_history.append({
                "query": user_query,
                "recommendations": result["recommendations"],
                "relaxation_notice": result["relaxation_notice"]
            })

    # Display Current Recommendations
    if st.session_state.last_recommendations:
        latest = st.session_state.chat_history[-1] if st.session_state.chat_history else None
        if latest and latest.get("relaxation_notice"):
            st.info(latest["relaxation_notice"])

        st.markdown(f"### 🎯 Top Recommendations ({len(st.session_state.last_recommendations)} matches)")

        # Render 2-column or 3-column responsive grid
        cols = st.columns(3)
        for i, item in enumerate(st.session_state.last_recommendations):
            col = cols[i % 3]
            with col:
                media_type_label = "Movie" if item.get("media_type") == "movie" else "TV Series"
                year_label = str(item.get("release_year") or "Year N/A")
                rating_val = item.get("rating")
                rating_str = f"★ {rating_val}/10" if rating_val is not None else "★ Not rated"
                match_pct = item.get("match_percentage", 85)
                runtime_str = item.get("runtime_or_episodes") or "Not available"
                lang_str = (item.get("original_language") or "en").upper()

                # Card HTML
                poster_url = item.get("poster_path")
                if poster_url:
                    poster_html = f'<img src="{poster_url}" style="width:100%; height:320px; object-fit:cover; border-radius:12px 12px 0 0;" alt="{item.get("title")}">'
                else:
                    poster_html = f'<div class="poster-placeholder"><span>🎬</span><br><strong>{item.get("title")}</strong><br><small>Poster not available</small></div>'

                genres_html = "".join([f'<span class="genre-chip">{g}</span>' for g in item.get("genres", [])[:3]])

                card_html = f"""
                <div class="movie-card">
                    {poster_html}
                    <div class="card-content">
                        <div class="card-title">{item.get('title')}</div>
                        <div class="card-meta">
                            <span class="badge-type">{media_type_label}</span>
                            <span class="badge-rating">{rating_str}</span>
                            <span class="badge-match">{match_pct}% Match</span>
                            <span>• {year_label}</span>
                            <span>• {lang_str}</span>
                            <span>• {runtime_str}</span>
                        </div>
                        <div style="margin-bottom: 0.6rem;">{genres_html}</div>
                        <div class="card-overview">{item.get('overview', 'No overview provided.')}</div>
                        <div class="why-match-box">
                            💡 <strong>Why this matches you:</strong><br>
                            {item.get('ai_explanation', 'Curated according to your tastes.')}
                        </div>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

                # Action Buttons
                btn_col1, btn_col2 = st.columns([1, 1])
                in_watch = is_in_watchlist(item["id"])
                with btn_col1:
                    if in_watch:
                        if st.button("✓ In Watchlist", key=f"remove_btn_{item['id']}_{i}", use_container_width=True):
                            remove_from_watchlist(item["id"])
                            st.rerun()
                    else:
                        if st.button("+ Watchlist", key=f"add_btn_{item['id']}_{i}", use_container_width=True):
                            add_to_watchlist(item)
                            st.rerun()

                with btn_col2:
                    tmdb_link = item.get("tmdb_url")
                    if tmdb_link:
                        st.link_button("TMDB Info ↗", tmdb_link, use_container_width=True)

                # Similar Titles Expander
                with st.expander(f"🔍 Similar to {item.get('title')}"):
                    similar_items = engine.get_similar_titles(item["id"], item.get("media_type", "movie"), top_n=3)
                    if similar_items:
                        for sim in similar_items:
                            st.markdown(f"**{sim.get('title')}** ({sim.get('release_year', 'N/A')}) • ★ {sim.get('rating', 'N/A')}/10")
                            st.caption(sim.get("overview", "")[:120] + "...")
                    else:
                        st.caption("No similar titles found.")

                st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    else:
        # Welcome Empty State
        st.markdown(
            """
            <div style="background: #131926; border: 1px dashed #334155; border-radius: 12px; padding: 2.5rem; text-align: center; margin-top: 1.5rem;">
                <h3 style="color: #f1f5f9; margin-bottom: 0.5rem;">Ready to find your next favorite title?</h3>
                <p style="color: #94a3b8; max-width: 600px; margin: 0 auto 1.5rem auto;">
                    Tell CineMate what you are in the mood for — mention specific genres, unexpected plot twists, emotional endings, or reference movies like <em>Interstellar</em> or <em>Shutter Island</em>.
                </p>
                <div style="display: flex; justify-content: center; gap: 8px; flex-wrap: wrap;">
                    <span class="taste-chip">✨ Mind-bending Sci-Fi</span>
                    <span class="taste-chip">🍿 Weekend Binge Series</span>
                    <span class="taste-chip">🇮🇳 Indian Suspense Dramas</span>
                    <span class="taste-chip">❤️ Heartwarming Rom-Coms</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


with tab_watchlist:
    st.markdown("### 🔖 Your Personal Watchlist")
    st.caption("Saved titles persist locally in your SQLite database.")

    saved_items = get_watchlist()
    if not saved_items:
        st.markdown(
            """
            <div style="background: #131926; border: 1px dashed #334155; border-radius: 12px; padding: 3rem; text-align: center;">
                <h4>Your watchlist is empty</h4>
                <p style="color: #94a3b8;">Discover titles and click <strong>+ Watchlist</strong> to save them for later.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        filter_col1, filter_col2 = st.columns([3, 1])
        with filter_col1:
            watch_filter = st.selectbox("Filter Watchlist By", ["All Titles", "Movies Only", "TV Series Only"])

        filtered_watchlist = saved_items
        if watch_filter == "Movies Only":
            filtered_watchlist = [x for x in saved_items if x.get("media_type") == "movie"]
        elif watch_filter == "TV Series Only":
            filtered_watchlist = [x for x in saved_items if x.get("media_type") == "tv"]

        st.markdown(f"Showing **{len(filtered_watchlist)}** titles:")

        for item in filtered_watchlist:
            w_col1, w_col2, w_col3 = st.columns([1, 4, 1])
            with w_col1:
                p_url = item.get("poster_path")
                if p_url:
                    st.image(p_url, use_container_width=True)
                else:
                    st.markdown("🎬 *No Poster*")
            with w_col2:
                media_label = "Movie" if item.get("media_type") == "movie" else "TV Series"
                st.markdown(f"#### {item.get('title')} ({item.get('release_year', 'N/A')})")
                st.markdown(f"<span class='badge-type'>{media_label}</span> <span class='badge-rating'>★ {item.get('rating', 'N/A')}/10</span>", unsafe_allow_html=True)
                genres_list = item.get("genres", [])
                if genres_list:
                    st.caption(f"🎭 Genres: {', '.join(genres_list)}")
                st.write(item.get("overview", "")[:200] + "...")
                if item.get("tmdb_url"):
                    st.markdown(f"[View on TMDB ↗]({item.get('tmdb_url')})")
            with w_col3:
                st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Remove", key=f"del_watch_{item['id']}", use_container_width=True):
                    remove_from_watchlist(item["id"])
                    st.rerun()
            st.divider()
