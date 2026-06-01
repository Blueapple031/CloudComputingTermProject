"""dummy-web API 테스트."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    """헬스체크는 200과 status=ok 를 반환해야 한다."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "dummy-web"


def test_load_returns_instance_header():
    """CPU 부하 엔드포인트는 X-Instance-Id 헤더를 포함한다."""
    response = client.get("/api/load?ms=10")
    assert response.status_code == 200
    assert "X-Instance-Id" in response.headers
    assert response.json()["ok"] is True


def test_db_sim_returns_ok():
    """DB 시뮬 엔드포인트 기본 동작."""
    response = client.get("/api/db-sim?delay_ms=10")
    assert response.status_code == 200
    assert response.json()["ok"] is True
