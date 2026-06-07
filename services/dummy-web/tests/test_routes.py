"""dummy-web API 테스트."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "dummy-web"


def test_load_returns_instance_header():
    response = client.get("/api/load?ms=10")
    assert response.status_code == 200
    assert "X-Instance-Id" in response.headers
    assert response.json()["ok"] is True


def test_db_sim_returns_ok():
    response = client.get("/api/db-sim?delay_ms=10")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_metrics_returns_cpu_fields():
    """CPU 사용률·가용률 필드가 JSON 에 포함된다."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "dummy-web"
    assert "cpu_percent" in body
    assert "cpu_available_percent" in body
    assert 0 <= body["cpu_percent"] <= 100
    assert body["cpu_available_percent"] == round(100 - body["cpu_percent"], 2)
    assert "requests" in body


def test_dashboard_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "CPU" in response.text
    assert "/api/metrics" in response.text
