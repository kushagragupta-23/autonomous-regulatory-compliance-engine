import pytest
from backend.services.scoring_engine import (
    TenSignalHybridScorer,
    ScoringConfig,
    SignalResult
)
from backend.models.clients import PRESET_CLIENTS

def test_ten_signal_scoring_kushagra_tech():
    scorer = TenSignalHybridScorer()
    client = PRESET_CLIENTS[0]  # Kushagra Technologies Pvt Ltd (IT / Software Services)

    update = {
        "id": "SCRAPE_test_001",
        "title": "Circular No. 14/2026: Clarifications on TDS Withholding under Section 194R on Business Incentives",
        "authority": "CBDT (Income Tax)",
        "statute": "Income Tax",
        "doc_type": "Circular",
        "summary": "Mandatory 10% TDS deduction under Section 194R on incentives exceeding INR 20,000 for IT/ITES companies.",
        "full_text": "CBDT issues guidelines for software companies and ITES on Section 194R TDS withholding.",
        "sectors": ["IT / Software Services"],
        "topics": ["TDS / TCS Withholding"],
        "sections": ["Section 194R"],
        "urgency": "High",
        "published_date": "02 November 2026",
        "scraped_at": "2026-11-03 01:00:00 UTC"
    }

    result = scorer.score(update, client, client.get("assigned_lead"))

    assert "score_100" in result
    assert result["score_100"] >= 65.0
    assert result["urgency_tier"] in ["CRITICAL", "ELEVATED"]
    assert len(result["signals"]) >= 9
    assert result["signals"]["section"] > 0.0
    assert result["signals"]["industry"] > 0.0
    assert len(result["reasons"]) >= 2
    assert "✓" in result["explanation"]
    assert "suggested_task" in result
    assert result["suggested_task"]["priority"] in ["P1 - Critical", "P2 - Elevated"]

def test_task_workflow_api():
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    # 1. Fetch feed to populate tasks
    feed_resp = client.get("/api/v1/feed?client_id=client_kushagra_tech")
    assert feed_resp.status_code == 200
    feed_data = feed_resp.json()
    assert len(feed_data["feed"]) > 0

    first_item = feed_data["feed"][0]
    task_id = first_item["suggested_task"]["task_id"]

    # 2. Query task endpoint
    tasks_resp = client.get("/api/v1/tasks?client_id=client_kushagra_tech")
    assert tasks_resp.status_code == 200
    tasks_data = tasks_resp.json()
    assert tasks_data["total_tasks"] > 0

    # 3. Approve task
    action_resp = client.post(f"/api/v1/tasks/{task_id}/action", json={"action": "APPROVE"})
    assert action_resp.status_code == 200
    assert action_resp.json()["action_taken"] == "APPROVE"
    assert action_resp.json()["updated_task"]["status"] == "APPROVED_SCHEDULED"
