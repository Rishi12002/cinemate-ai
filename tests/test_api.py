"""
test_api.py - Unit and integration tests for Vercel Serverless API endpoints
"""

import pytest
from starlette.testclient import TestClient
from api.index import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["name"] == "CineMate AI"
    assert "is_demo_mode" in data
    assert data["catalog_size"] > 0


def test_api_recommend_missing_query():
    response = client.post("/api/recommend", json={})
    assert response.status_code == 400


def test_api_recommend_success():
    payload = {
        "query": "Recommend mind-bending sci-fi movies with unexpected endings."
    }
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["recommendations"]) > 0
    top = data["recommendations"][0]
    assert "title" in top
    assert "match_percentage" in top
    assert "ai_explanation" in top


def test_api_recommend_followup():
    # Turn 1
    t1 = client.post("/api/recommend", json={"query": "Recommend 5 psychological thrillers."}).json()
    assert t1["success"] is True
    prefs = t1["preferences"]

    # Turn 2
    t2 = client.post("/api/recommend", json={
        "query": "Only Indian ones.",
        "preferences": prefs
    }).json()
    assert t2["success"] is True
    assert t2["preferences"]["country_or_industry"] == "India"
    assert "Thriller" in t2["preferences"]["genres"]


def test_api_similar():
    response = client.get("/api/similar?id=157336&media_type=movie")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "similar_titles" in data
