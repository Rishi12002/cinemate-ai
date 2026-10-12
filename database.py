"""
database.py - Persistent Watchlist Storage via SQLite
CineMate AI - "Your taste. Your next obsession."
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "watchlist.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a connection to the SQLite database and ensure directory exists."""
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the watchlist table schema if it does not already exist."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tmdb_id INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL,
                media_type TEXT NOT NULL,
                release_year INTEGER,
                rating REAL,
                genres TEXT,
                overview TEXT,
                poster_path TEXT,
                runtime_or_episodes TEXT,
                tmdb_url TEXT,
                added_at TEXT NOT NULL
            )
        """)
        conn.commit()


def add_to_watchlist(item: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """
    Add a movie or series to the watchlist.
    Returns True if added, False if already exists or on failure.
    """
    init_db(db_path)
    tmdb_id = item.get("id") or item.get("tmdb_id")
    if not tmdb_id:
        return False

    title = item.get("title", "Untitled")
    media_type = item.get("media_type", "movie")
    release_year = item.get("release_year")
    rating = item.get("rating")
    genres = item.get("genres", [])
    if isinstance(genres, list):
        genres_json = json.dumps(genres)
    else:
        genres_json = json.dumps([str(genres)])

    overview = item.get("overview", "")
    poster_path = item.get("poster_path", "")
    runtime_or_episodes = item.get("runtime_or_episodes", "")
    tmdb_url = item.get("tmdb_url", "")
    added_at = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO watchlist 
                (tmdb_id, title, media_type, release_year, rating, genres, overview, poster_path, runtime_or_episodes, tmdb_url, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tmdb_id, title, media_type, release_year, rating, genres_json, overview, poster_path, runtime_or_episodes, tmdb_url, added_at))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return False


def remove_from_watchlist(tmdb_id: int, db_path: Optional[str] = None) -> bool:
    """
    Remove an item from the watchlist by tmdb_id.
    Returns True if deleted, False otherwise.
    """
    init_db(db_path)
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist WHERE tmdb_id = ?", (tmdb_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return False


def is_in_watchlist(tmdb_id: int, db_path: Optional[str] = None) -> bool:
    """Check if an item is currently saved in the watchlist."""
    init_db(db_path)
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM watchlist WHERE tmdb_id = ?", (tmdb_id,))
            return cursor.fetchone() is not None
    except Exception:
        return False


def get_watchlist(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all items in the watchlist ordered by addition time descending."""
    init_db(db_path)
    items = []
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM watchlist ORDER BY id DESC")
            rows = cursor.fetchall()
            for r in rows:
                item = dict(r)
                # Unpack genres json
                try:
                    item["genres"] = json.loads(item["genres"]) if item["genres"] else []
                except Exception:
                    item["genres"] = []
                item["id"] = item["tmdb_id"]
                items.append(item)
    except Exception as e:
        print(f"Error fetching watchlist: {e}")
    return items


def clear_watchlist(db_path: Optional[str] = None) -> bool:
    """Clear all records from watchlist (useful for test resets)."""
    init_db(db_path)
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist")
            conn.commit()
            return True
    except Exception:
        return False
