def _start_session(client, headers):
    resp = client.post(
        "/api/session/start",
        json={"app_name": "Instagram", "device_model": "iQOO 13", "android_version": "15"},
        headers=headers,
    )
    return resp.json()["data"]["session_id"]


def test_create_interaction(client, auth_headers):
    headers = auth_headers("i1@example.com")
    session_id = _start_session(client, headers)
    resp = client.post(
        "/api/interactions",
        json={
            "session_id": session_id,
            "action_type": "CLICK",
            "screen_name": "LoginScreen",
            "action_data": {"x": 250, "y": 500},
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["action_type"] == "CLICK"


def test_retrieve_interactions(client, auth_headers):
    headers = auth_headers("i2@example.com")
    session_id = _start_session(client, headers)
    for action in ("CLICK", "SCROLL"):
        client.post(
            "/api/interactions",
            json={
                "session_id": session_id,
                "action_type": action,
                "screen_name": "HomeScreen",
                "action_data": {},
            },
            headers=headers,
        )
    resp = client.get(f"/api/interactions/session/{session_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_interactions_ordering(client, auth_headers):
    headers = auth_headers("i3@example.com")
    session_id = _start_session(client, headers)
    client.post(
        "/api/interactions",
        json={
            "session_id": session_id,
            "action_type": "CLICK",
            "screen_name": "HomeScreen",
            "action_data": {},
            "sequence_number": 2,
        },
        headers=headers,
    )
    client.post(
        "/api/interactions",
        json={
            "session_id": session_id,
            "action_type": "SWIPE",
            "screen_name": "HomeScreen",
            "action_data": {},
            "sequence_number": 1,
        },
        headers=headers,
    )
    resp = client.get(f"/api/interactions/session/{session_id}", headers=headers)
    data = resp.json()["data"]
    assert [d["sequence_number"] for d in data] == [1, 2]
    assert data[0]["action_type"] == "SWIPE"
