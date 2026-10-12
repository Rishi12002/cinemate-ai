"""
api/index.py - Vercel Serverless ASGI Handler for CineMate AI
Exposes REST endpoints for movie/series recommendation and similarity search.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path for Vercel execution environment
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from recommender import RecommenderEngine
from preferences import UserPreferences
from tmdb_client import TMDBClient
from ai_agent import AIAgent

# Initialize recommendation engine
engine = RecommenderEngine()


async def health(request):
    """Health check endpoint returning engine status."""
    return JSONResponse({
        "status": "healthy",
        "name": "CineMate AI",
        "tagline": "Your taste. Your next obsession.",
        "is_demo_mode": engine.is_demo_mode(),
        "catalog_size": len(engine.sample_catalogue)
    })


async def recommend(request):
    """
    POST /api/recommend
    Body: {"query": str, "preferences": Optional[dict]}
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    query = body.get("query", "").strip()
    if not query:
        return JSONResponse({"error": "Query string is required."}, status_code=400)

    raw_prefs = body.get("preferences")
    current_prefs = None
    if raw_prefs and isinstance(raw_prefs, dict):
        try:
            current_prefs = UserPreferences.from_dict(raw_prefs)
        except Exception:
            current_prefs = None

    try:
        result = engine.recommend(user_message=query, current_preferences=current_prefs)
        response_data = {
            "success": True,
            "query": query,
            "preferences": result["preferences"].to_dict(),
            "summary_chips": result["preferences"].summary_chips(),
            "recommendations": result["recommendations"],
            "is_demo_mode": result["is_demo_mode"],
            "relaxation_notice": result["relaxation_notice"],
            "total_matches": result["total_matches"]
        }
        return JSONResponse(response_data)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def similar(request):
    """
    GET /api/similar?id=123&media_type=movie
    """
    item_id_str = request.query_params.get("id")
    media_type = request.query_params.get("media_type", "movie")

    if not item_id_str:
        return JSONResponse({"error": "Missing item id."}, status_code=400)

    try:
        item_id = int(item_id_str)
    except ValueError:
        return JSONResponse({"error": "Invalid item id."}, status_code=400)

    sims = engine.get_similar_titles(item_id, media_type, top_n=4)
    return JSONResponse({"success": True, "similar_titles": sims})


routes = [
    Route("/api/health", health, methods=["GET"]),
    Route("/api/recommend", recommend, methods=["POST"]),
    Route("/api/similar", similar, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(routes=routes, middleware=middleware)
