from app.routes.health import health_check


def test_health_endpoint():
    response = health_check()
    assert response["status"] == "ok"
    assert response["service"] == "opsrecall-ai"
