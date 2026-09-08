def _start_session(client, headers):
    resp = client.post(
        "/api/session/start",
        json={"app_name": "Instagram", "device_model": "iQOO 13", "android_version": "15"},
        headers=headers,
    )
    return resp.json()["data"]["session_id"]


def _metric_payload(session_id, **overrides):
    payload = {
        "session_id": session_id,
        "fps": 58.5,
        "memory_usage": 72.4,
        "battery_usage": 3.2,
        "cpu_usage": 64.7,
        "temperature": 38.5,
        "frame_drops": 4,
    }
    payload.update(overrides)
    return payload


def test_create_metric(client, auth_headers):
    headers = auth_headers("m1@example.com")
    session_id = _start_session(client, headers)
    resp = client.post("/api/metrics", json=_metric_payload(session_id), headers=headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["fps"] == 58.5


def test_get_session_metrics_ordered(client, auth_headers):
    headers = auth_headers("m2@example.com")
    session_id = _start_session(client, headers)
    client.post("/api/metrics", json=_metric_payload(session_id, fps=50), headers=headers)
    client.post("/api/metrics", json=_metric_payload(session_id, fps=55), headers=headers)
    resp = client.get(f"/api/metrics/session/{session_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    timestamps = [m["recorded_at"] for m in data]
    assert timestamps == sorted(timestamps)


def test_metric_validation_failure(client, auth_headers):
    headers = auth_headers("m3@example.com")
    session_id = _start_session(client, headers)
    resp = client.post(
        "/api/metrics", json=_metric_payload(session_id, cpu_usage=150), headers=headers
    )
    assert resp.status_code == 422


def test_metric_negative_fps_rejected(client, auth_headers):
    headers = auth_headers("m4@example.com")
    session_id = _start_session(client, headers)
    resp = client.post("/api/metrics", json=_metric_payload(session_id, fps=-1), headers=headers)
    assert resp.status_code == 422
