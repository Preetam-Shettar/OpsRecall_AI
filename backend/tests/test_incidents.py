from fastapi.testclient import TestClient

from app.main import app


def test_create_incident_returns_analysis():
    with TestClient(app) as client:
        response = client.post(
            "/api/incidents",
            json={
                "title": "Orders API returning 500 errors",
                "service": "orders-api",
                "environment": "staging",
                "description": "Requests began failing after the latest deployment.",
                "logs": "Database connection acquisition timed out after 30 seconds.",
                "deployment_context": "Release 1.4.2",
            },
        )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "incident_id" in payload
    assert payload["analysis"]["summary"]
    assert payload["recommendations"]
