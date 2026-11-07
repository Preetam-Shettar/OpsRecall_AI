import httpx
from app.services.hindsight_service import HindsightMemoryClient


def test_hindsight_retain_and_recall_local(tmp_path, monkeypatch):
    test_db = tmp_path / "test_opsrecall.db"
    monkeypatch.setattr("app.database.DATABASE_PATH", test_db)
    from app.database import init_db
    init_db()

    client = HindsightMemoryClient()
    client.base_url = None
    client.api_key = None

    retain_res = client.retain(
        content="Incident INC-001: Connection pool exhausted. Resolved by raising pool max from 10 to 40.",
        incident_id="INC-001",
        service="orders-api",
        outcome="resolved",
    )
    assert retain_res["status"] == "stored_locally"

    results = client.recall("connection pool orders-api")
    assert len(results) > 0
    assert "INC-001" in results[0]["content"]

    summary = client.reflect("connection pool")
    assert "INC-001" in summary


def test_hindsight_api_dispatch(tmp_path, monkeypatch):
    test_db = tmp_path / "test_opsrecall_api.db"
    monkeypatch.setattr("app.database.DATABASE_PATH", test_db)
    from app.database import init_db
    init_db()

    client = HindsightMemoryClient()
    client.base_url = "https://api.hindsight.test"
    client.api_key = "test-token"

    def fake_post(url, **kwargs):
        if url.endswith("/retain"):
            return httpx.Response(200, json={"status": "retained", "id": "mem_123"}, request=httpx.Request("POST", url))
        if url.endswith("/recall"):
            return httpx.Response(
                200,
                json={"results": [{"incident_id": "INC-001", "content": "Pool limit increased"}]},
                request=httpx.Request("POST", url),
            )
        if url.endswith("/reflect"):
            return httpx.Response(200, json={"text": "Historical lesson summary"}, request=httpx.Request("POST", url))
        return httpx.Response(404, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)

    ret = client.retain("Test memory", incident_id="INC-999")
    assert ret["source"] == "hindsight_api"

    rec = client.recall("test")
    assert len(rec) == 1
    assert rec[0]["source"] == "hindsight_api"

    ref = client.reflect("test")
    assert ref == "Historical lesson summary"
