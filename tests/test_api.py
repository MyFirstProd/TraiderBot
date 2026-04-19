import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "x" * 32
os.environ["ADMIN_API_KEY"] = "y" * 32
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:telegram-token-for-tests"

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_admin_requires_api_key():
    with TestClient(app) as client:
        response = client.get("/api/v1/admin/config")
        assert response.status_code == 403


def test_dashboard_endpoint_returns_payload():
    with TestClient(app) as client:
        response = client.get("/api/v1/telegram/dashboard")
        assert response.status_code == 200
        payload = response.json()
        assert "equity" in payload
        assert "snapshots" in payload
        assert "model" in payload
