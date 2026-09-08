import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def clean_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    def _register_and_login(email: str = "jane@example.com", password: str = "password123"):
        client.post(
            "/api/auth/register",
            json={"name": "Jane Doe", "email": email, "password": password},
        )
        login_resp = client.post("/api/auth/login", json={"email": email, "password": password})
        token = login_resp.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _register_and_login
