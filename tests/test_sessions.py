def _start_session(client, headers):
    return client.post(
        "/api/session/start",
        json={"app_name": "Instagram", "device_model": "iQOO 13", "android_version": "15"},
        headers=headers,
    )


def test_start_session(client, auth_headers):
    headers = auth_headers("s1@example.com")
    resp = _start_session(client, headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == "STARTED"
    assert data["session_id"]


def test_get_session(client, auth_headers):
    headers = auth_headers("s2@example.com")
    session_id = _start_session(client, headers).json()["data"]["session_id"]
    resp = client.get(f"/api/session/{session_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["session_id"] == session_id


def test_end_session(client, auth_headers):
    headers = auth_headers("s3@example.com")
    session_id = _start_session(client, headers).json()["data"]["session_id"]
    resp = client.put(
        "/api/session/end", json={"session_id": session_id, "status": "COMPLETED"}, headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "COMPLETED"
    assert data["end_time"] is not None


def test_end_session_twice_fails(client, auth_headers):
    headers = auth_headers("s4@example.com")
    session_id = _start_session(client, headers).json()["data"]["session_id"]
    client.put("/api/session/end", json={"session_id": session_id, "status": "COMPLETED"}, headers=headers)
    resp = client.put(
        "/api/session/end", json={"session_id": session_id, "status": "COMPLETED"}, headers=headers
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "SESSION_ALREADY_COMPLETED"


def test_get_nonexistent_session(client, auth_headers):
    headers = auth_headers("s5@example.com")
    resp = client.get("/api/session/does-not-exist", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "SESSION_NOT_FOUND"


def test_cannot_access_other_users_session(client, auth_headers):
    owner_headers = auth_headers("owner@example.com")
    session_id = _start_session(client, owner_headers).json()["data"]["session_id"]

    other_headers = auth_headers("intruder@example.com")
    resp = client.get(f"/api/session/{session_id}", headers=other_headers)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "UNAUTHORIZED_SESSION_ACCESS"
