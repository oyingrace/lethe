import pytest
from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_qwen_check_degrades_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    response = client.get("/qwen-check")

    assert response.status_code == 200
    body = response.json()
    assert body["degraded"] is True
    assert "error" in body
