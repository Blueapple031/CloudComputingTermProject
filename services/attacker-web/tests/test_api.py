"""attacker-web 테스트."""

import pytest
from fastapi.testclient import TestClient

from app.load_generator import LoadGenerator
from app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "attacker-web" in response.text


def test_start_rejects_invalid_host():
    """화이트리스트에 없는 호스트는 400."""
    response = client.post(
        "/api/load/start",
        json={"target_url": "http://evil.example.com/api/load", "rps": 10},
    )
    assert response.status_code == 400


def test_load_generator_validate_url():
    gen = LoadGenerator()
    with pytest.raises(ValueError, match="허용되지 않은"):
        gen._validate_target_url("http://not-allowed.com/")
