# CineMate AI — Movie & Web Series Recommendation Agent
> *"Your taste. Your next obsession."*

CineMate AI is a production-ready, beginner-friendly movie and web series recommendation agent designed to help users discover cinematic gems through natural-language requests, mood, viewing interests, and contextual follow-ups.

---

## 🌟 Key Features

- **Natural Language Discovery**: Understands nuanced requests such as *"Mind-bending sci-fi with twist endings"*, *"Indian crime web series with suspense"*, or *"Psychological thriller like Shutter Island"*.
- **Multi-Turn Conversational Memory**: Preserves user constraints across follow-ups (e.g., Turn 1: *"5 psychological thrillers"* ➔ Turn 2: *"Only Indian ones"* ➔ Turn 3: *"Released after 2020"* ➔ Turn 4: *"Less disturbing"*).
- **Hybrid Recommendation Engine**:
  - **Hard Constraints**: Strict filtering on media type, release year, language, country, runtime, and content restrictions.
  - **Transparent 7-Factor Weighted Scoring**: Formula combining genre overlap, semantic TF-IDF plot similarity, mood, verified rating, language, release year, and runtime.
- **Dual Operating Modes**:
  - **🟣 Demo Mode (Curated Catalogue)**: Works out-of-the-box with 45+ verified international titles across Hollywood, Indian Cinema (Bollywood/Tollywood), Korean Dramas, Anime, and British series.
  - **🟢 Live Mode**: Connects directly to TMDB API for infinite titles and Google Gemini GenAI SDK for AI interpretation.
- **Grounded AI Explanations**: Generates spoiler-free, metadata-grounded *"Why this matches you"* explanations for every title.
- **Persistent Local Watchlist**: SQLite database (`data/watchlist.db`) allowing users to bookmark, view, and manage saved titles across sessions.
- **Dark Streaming Interface**: Responsive dark charcoal theme inspired by premium streaming platforms with poster cards, verified rating badges, genre pills, and similar title discovery.

---

## 📐 Architecture Overview

```
User Natural Language Query
          │
          ▼
┌──────────────────────────────────────────────┐
│       Streamlit Interface (app.py)          │
│   • Conversational Chat & Prompt Chips       │
│   • Multi-Turn Memory Display                │
│   • Card Grid with Posters & Match %         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          AI Agent (ai_agent.py)              │
│   • Gemini GenAI SDK (gemini-2.5-flash)      │
│   • Robust Pattern-Matching NLP Fallback     │
│   • Extracts Structured UserPreferences      │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│    Recommendation Engine (recommender.py)    │
│   • Candidate Retrieval (TMDB or Sample Cat) │
│   • Hard Constraint Filtering (Type/Year/etc)│
│   • 7-Factor Weighted Scoring & Ranking      │
│   • Grounded Explanation Generation          │
└──────────────────────┬───────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│   TMDB Client    │      │ SQLite Watchlist │
│ (tmdb_client.py) │      │  (database.py)   │
└──────────────────┘      └──────────────────┘
```

---

## ⚖️ Recommendation Scoring Breakdown

CineMate AI utilizes a transparent 7-factor mathematical scoring model:

| Factor | Weight | Evaluation Method |
| :--- | :---: | :--- |
| **Genre Match** | **30%** | Jaccard overlap between requested genres and title genres. |
| **Theme & Plot Similarity** | **25%** | TF-IDF vectorization and Cosine Similarity comparing query themes with title overview and keywords. |
| **Mood & Tone Match** | **15%** | Direct alignment with requested moods (e.g. *mind-bending*, *dark*, *wholesome*, *funny*). |
| **Verified User Rating** | **10%** | Normalized TMDB vote average ($\text{rating} / 10.0$). |
| **Language & Regional Origin** | **10%** | Country code and language match (e.g. India/Hindi, South Korea/Korean). |
| **Release Year Proximity** | **5%** | Proximity function to requested era or target year bounds. |
| **Runtime Match** | **5%** | Normalized fit within user runtime limit (e.g. $<110$ min or short series). |

$$\text{Composite Score} = 0.30 G + 0.25 T + 0.15 M + 0.10 R + 0.10 L + 0.05 Y + 0.05 Rt$$

---

## 🤖 AI Interpretation vs. Factual Metadata Retrieval

A critical design principle of CineMate AI is the separation of concerns between AI and metadata:

1. **AI Interpretation (Gemini)**:
   - Interprets subjective natural language (e.g., *"mind-bending"*, *"for a bad day"*, *"something less disturbing"*).
   - Resolves conversational context across follow-up queries.
   - Formulates clear, grounded explanations.
2. **Factual Metadata Retrieval (TMDB / Verified Catalogue)**:
   - Provides factual ratings, release dates, runtimes, cast, and high-resolution posters.
   - **Prevents Hallucinations**: CineMate never allows an LLM to invent titles, fake ratings, or fabricate plot twists.

---

## 🚀 Quickstart Guide (macOS & VS Code)

### Prerequisites
- macOS with Python 3.10+ (tested on Python 3.14)
- Visual Studio Code or your preferred editor
- Terminal

### Step 1: Clone or Navigate to the Project
```bash
cd /Users/rishiadhikarig/Documents/Anitgarvity/cinemate-ai
```

### Step 2: Create and Activate Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate on macOS / Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: (Optional) Configure API Keys for Live Mode
By default, CineMate AI runs in **Demo Mode** with a rich 45+ item curated dataset without requiring any API keys.

To enable **Live Mode** with real-time TMDB and Gemini GenAI:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your keys:
   - **TMDB API Key**: Obtain a free key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api).
   - **Google Gemini API Key**: Obtain a free key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

```env
TMDB_API_KEY=your_actual_tmdb_key_here
GEMINI_API_KEY=your_actual_gemini_key_here
```

### Step 5: Run the Streamlit Application
```bash
streamlit run app.py
```
Streamlit will launch automatically in your browser at:
`http://localhost:8501`

### Step 6: Run Automated Tests
```bash
pytest tests/ -v
```
All 20 unit, integration, and API tests will execute and verify filters, multi-turn memory, SQLite persistence, and ranking.

---

## ☁️ Deploying to Vercel

CineMate AI is configured for native **Vercel Serverless** deployment with a Python serverless backend (`api/index.py`), static dark-mode streaming web app (`public/index.html`), and `vercel.json` routing.

### Option A: 1-Click Deploy via Vercel CLI (Recommended)
From inside the `cinemate-ai` folder, run:
```bash
npx vercel
```
1. Follow the interactive prompts (press Enter to accept default settings).
2. To deploy directly to production:
   ```bash
   npx vercel --prod
   ```
3. Vercel will output your live URL (e.g., `https://cinemate-ai-xxx.vercel.app`).

### Option B: Deploy via GitHub & Vercel Dashboard
1. Initialize a git repository and push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Deploy CineMate AI to Vercel"
   # Link to your remote GitHub repo
   git remote add origin https://github.com/your-username/cinemate-ai.git
   git branch -M main
   git push -u origin main
   ```
2. Go to [vercel.com/new](https://vercel.com/new) and click **Import** next to your repository.
3. (Optional) Add your API keys under **Environment Variables**:
   - `TMDB_API_KEY`
   - `GEMINI_API_KEY`
   *(If omitted, the app runs automatically in Demo Mode with the 45+ item curated catalogue!)*
4. Click **Deploy**. Vercel will build and launch your live app with global CDN distribution!

---

## 🧪 Testing Scenarios Supported Out-of-the-Box

Try these queries in the search bar or click the prompt chips:
1. *"Recommend mind-bending sci-fi movies with unexpected endings."*
2. *"I want a psychological thriller like Shutter Island."*
3. *"Suggest Indian web series with suspense and strong storytelling."*
4. *"Recommend romantic movies that are emotional but have a happy ending."*
5. *"Give me the best horror movies without too much gore."*
6. *"Recommend something funny for a bad day."*
7. *"Find English sci-fi movies released after 2020."*
8. *"Suggest a series with short episodes that I can finish this weekend."*
9. *"Recommend movies similar to Interstellar, Inception, or The Prestige."*
10. **Multi-turn Test**: Ask *"Recommend five psychological thrillers"*, then follow up with *"Only Indian ones"*, then *"Released after 2020"*, and finally *"Give me something less disturbing"*.

---

## 🛠️ Troubleshooting Common Issues

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'streamlit'` | Virtual environment not active | Run `source venv/bin/activate` before starting the app. |
| `Port 8501 is already in use` | Another Streamlit process is running | Run `streamlit run app.py --server.port 8502` to use another port. |
| `TMDB API warning: HTTP 401` | Invalid TMDB API key in `.env` | Check `.env` or leave empty to use offline Demo Mode. |
| `Watchlist not saving` | SQLite folder permission | Ensure `data/` folder exists and is writable. |

---

## 📁 Project Structure

```
cinemate-ai/
├── app.py                   # Streamlit frontend & interactive UI
├── recommender.py           # Hybrid recommendation engine & scoring
├── ai_agent.py              # Gemini GenAI SDK client & rule-based parser
├── tmdb_client.py           # TMDB REST client service
├── preferences.py           # UserPreferences model & multi-turn memory
├── database.py              # SQLite persistent watchlist storage
├── requirements.txt         # Project dependencies
├── .env.example             # Example environment variable file
├── .gitignore               # Git ignore file
├── pytest.ini               # Pytest configuration
├── README.md                # Project documentation & guide
├── data/
│   ├── sample_catalogue.json# Curated 45+ item offline catalogue
│   └── watchlist.db         # Local SQLite watchlist database
└── tests/
    ├── conftest.py          # Pytest path setup
    ├── test_preferences.py  # Tests for preferences & conversational updates
    └── test_recommender.py  # Tests for filters, ranking, and database
```
