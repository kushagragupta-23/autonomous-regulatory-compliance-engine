import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_samples_endpoint():
    response = client.get("/api/v1/samples")
    assert response.status_code == 200
    samples = response.json()
    assert isinstance(samples, list)
    assert len(samples) >= 3

def test_analyze_endpoint():
    payload = {
        "circular_text": "Section 194R: 10% TDS on benefits and perquisites exceeding 20,000 INR.",
        "taxpayer_profile": {
            "entity_name": "Test Ventures Ltd",
            "entity_type": "Private_Limited",
            "annual_turnover": 40000000.0,
            "annual_income": 8000000.0,
            "industry_sector": "IT",
            "gst_registered": True,
            "opted_new_tax_regime": True,
            "employees_count": 25
        }
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert "impact_assessment" in data
    assert "audit_report" in data
    assert len(data["impact_assessment"]) > 0

def test_search_regulations():
    response = client.get("/api/v1/search?q=194R")
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data



def test_clients_endpoint():
    response = client.get("/api/v1/clients")
    assert response.status_code == 200
    clients = response.json()
    assert isinstance(clients, list)
    assert len(clients) >= 4
    assert any("Kushagra" in c["name"] for c in clients)

def test_personalized_feed_endpoint():
    response = client.get("/api/v1/feed?client_id=client_kushagra_tech")
    assert response.status_code == 200
    data = response.json()
    assert "feed" in data
    assert "client" in data
    assert len(data["feed"]) > 0
    first_item = data["feed"][0]
    assert "relevance_score" in first_item
    assert "client_impact" in first_item
    assert first_item["relevance_score"] >= 50.0

def test_scraper_trigger():
    response = client.post("/api/v1/scraper/trigger")
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["items_scraped"] > 0
