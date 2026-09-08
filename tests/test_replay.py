def _start_session(client, headers):
    resp = client.post(
        "/api/session/start",
        json={"app_name": "Instagram", "device_model": "iQOO 13", "android_version": "15"},
        headers=headers,
    )
    return resp.json()["data"]["session_id"]


def test_replay_chronological_ordering(client, auth_headers):
    headers = auth_headers("r1@example.com")
    session_id = _start_session(client, headers)

    for seq, action in [(1, "CLICK"), (2, "SCROLL"), (3, "TYPE"), (4, "BACK")]:
        client.post(
            "/api/interactions",
            json={
                "session_id": session_id,
                "action_type": action,
                "screen_name": "HomeScreen",
                "action_data": {},
                "sequence_number": seq,
            },
            headers=headers,
        )

    resp = client.get(f"/api/replay/{session_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_actions"] == 4
    assert [a["sequence_number"] for a in data["actions"]] == [1, 2, 3, 4]
    assert [a["action_type"] for a in data["actions"]] == ["CLICK", "SCROLL", "TYPE", "BACK"]


def test_replay_requires_ownership(client, auth_headers):
    owner_headers = auth_headers("owner2@example.com")
    session_id = _start_session(client, owner_headers)

    other_headers = auth_headers("intruder2@example.com")
    resp = client.get(f"/api/replay/{session_id}", headers=other_headers)
    assert resp.status_code == 403
