def test_register_user(client):
    resp = client.post(
        "/api/auth/register",
        json={"name": "John", "email": "john@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["email"] == "john@example.com"
    assert "password" not in body["data"]
    assert "password_hash" not in body["data"]


def test_duplicate_email_rejected(client):
    payload = {"name": "John", "email": "dupe@example.com", "password": "password123"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "USER_ALREADY_EXISTS"


def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={"name": "John", "email": "login@example.com", "password": "password123"},
    )
    resp = client.post("/api/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["access_token"]


def test_login_invalid_password(client):
    client.post(
        "/api/auth/register",
        json={"name": "John", "email": "wrongpw@example.com", "password": "password123"},
    )
    resp = client.post("/api/auth/login", json={"email": "wrongpw@example.com", "password": "nope12345"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "INVALID_CREDENTIALS"


def test_profile_requires_token(client):
    resp = client.get("/api/auth/profile")
    assert resp.status_code == 401


def test_profile_with_token(client, auth_headers):
    headers = auth_headers("profileuser@example.com")
    resp = client.get("/api/auth/profile", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "profileuser@example.com"
